require "digest"

module Attendances
  class ReceiveChannelMessage
    PRIORITIES = %w[basic intermediate advanced urgent].freeze

    def initialize(channel, data, body)
      @channel = channel
      @data = data
      @body = body
      @digest = Digest::SHA256.hexdigest(body)
      @entry_key = { channel_id: channel.id, source_event_id: data.fetch("source_event_id") }
    end

    def call
      entry = ChannelEntry.find_by(@entry_key)
      return receipt(entry) if entry

      SupportCase.transaction do
        HumanLocks.brand!(@channel.brand_id)
        conversation = ChannelConversation.create_or_find_by!(
          channel: @channel, external_conversation_id: @data.fetch("external_conversation_id")
        ) { |record| record.external_customer_id = @data.fetch("external_customer_id") }
        conversation.lock!
        entry = ChannelEntry.find_by(@entry_key)
        next receipt(entry) if entry

        if conversation.external_customer_id != @data.fetch("external_customer_id")
          raise WebhookV1::Error.new(409, "conversation_conflict", "A conversa pertence a outro cliente.")
        end

        support_case = current_case(conversation)
        message = support_case.append_message!(type: "customer", author_id: conversation.id,
                                               text: @data.fetch("text"), source_event_id: @entry_key[:source_event_id])
        previous_status = support_case.status
        if previous_status == "waiting_customer"
          status = support_case.assignee_id ? "waiting_resumption" : "waiting_human"
          support_case.advance!(status: status, human_queue_since: Time.current, blocking_reason: nil)
          support_case.audit!("case.human.customer_returned", actor_type: "customer", actor_id: conversation.id,
                              from_status: previous_status, message_id: message.id, assignee_id: support_case.assignee_id)
          DistributeHumanWorkJob.schedule(support_case.brand_id)
        else
          support_case.advance!
        end
        support_case.audit!("channel.message.received", actor_type: "customer", actor_id: conversation.id,
                            source_event_id: @entry_key[:source_event_id], message_id: message.id)
        if support_case.status == "ai_active" && support_case.integration_status == "idle" &&
            !support_case.turns.in_flight.exists?
          AgentIntegration::QueueTurn.call(support_case)
        end
        receipt(ChannelEntry.create!(**@entry_key, support_case: support_case, body_sha256: @digest, body: @body))
      end
    rescue ActiveRecord::RecordNotUnique
      entry = ChannelEntry.find_by(@entry_key)
      raise unless entry

      receipt(entry)
    end

    private

    def receipt(entry)
      if entry.body_sha256 != @digest
        raise WebhookV1::Error.new(409, "idempotency_conflict",
                                  "O ID de origem já foi aceito com outro conteúdo.",
                                  { source_event_id: @entry_key[:source_event_id] })
      end

      { case_id: entry.support_case_id, correlation_id: entry.support_case.correlation_id }
    end

    def current_case(conversation)
      previous = conversation.support_cases.order(created_at: :desc, id: :desc).lock.first
      return previous if previous && previous.status != "resolved"

      brand = @channel.brand
      queue = brand.support_queues.find_by!(active: true, is_default: true)
      status, classification = classify(brand)
      assignee = Operations::Attendant.find_by!(code: "mock", kind: "ai") if status == "ai_active"
      support_case = conversation.support_cases.create!(
        **classification, brand: brand, channel: @channel, queue: queue, assignee: assignee,
        status: status, previous_case_id: previous&.id, correlation_id: SecureRandom.uuid
      )
      support_case.audit!("case.opened", actor_type: "system", from_status: nil, queue_id: queue.id,
                          classification: support_case.classification, previous_case_id: previous&.id)
      support_case
    end

    def classify(brand)
      category, priority = @data.values_at("category", "priority")
      category_valid = category.is_a?(String) && category.match?(/\A[a-z][a-z0-9_]*\z/) &&
                       brand.categories.exists?(code: category, active: true)
      priority_valid = PRIORITIES.include?(priority)
      invalid = [[category, category_valid], [priority, priority_valid]].any? do |value, valid|
        ![nil, ""].include?(value) && !valid
      end
      status = if invalid
        "classification_review"
      elsif category_valid && priority_valid
        "ai_active"
      else
        "classification_pending"
      end

      [status, {
        category: category_valid ? category : nil, category_source: category_valid ? "channel" : nil,
        priority: priority_valid ? priority : nil, priority_source: priority_valid ? "channel" : nil
      }]
    end
  end
end
