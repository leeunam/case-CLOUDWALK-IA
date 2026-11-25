module Classification
  class CompleteRequest
    MAX_ATTEMPTS = 2
    LEASE = 30.seconds
    RETRY_DELAY = 1.second

    def initialize(request_id, classifier: ConfiguredJev)
      @request_id = request_id
      @classifier = classifier
    end

    def call
      claim = claim_attempt
      return unless claim

      attempt_id, categories, input = claim
      result = @classifier.call(categories: categories, **input)
      settle(attempt_id, result)
    end

    private

    def with_request
      Request.transaction do
        request = Request.find_by(id: @request_id)
        next unless request

        Attendances::HumanLocks.brand!(request.support_case.brand_id)
        record = Attendances::SupportCase.lock.find(request.support_case_id)
        request.lock!
        yield request, record
      end
    end

    def current?(request, record)
      request.completed_at.nil? && record.status == "classification_pending" &&
        record.classification_version == request.classification_version
    end

    def claim_attempt
      with_request do |request, record|
        next if request.completed_at || request.available_at.future?
        unless current?(request, record)
          request.update!(completed_at: Time.current)
          next
        end

        last = request.attempts.order(number: :desc).first
        if last && last.finished_at.nil?
          last.update!(finished_at: Time.current, disposition: "expired", issues: { provider: :worker_lease_expired })
        end
        if last && last.number >= MAX_ATTEMPTS
          last_issue = last.issues.values.first || "worker_lease_expired"
          review!(request, record, last_issue, last)
          next
        end

        message = record.messages.where(author_type: "customer").order(:sequence).first
        unless message
          review!(request, record, "missing_classification_text")
          next
        end

        attempt = request.attempts.create!(number: (last&.number || 0) + 1)
        request.update!(available_at: LEASE.from_now)
        [attempt.id, Catalog.categories(record.brand), { text: message.text, category: record.category, priority: record.priority }]
      end
    end

    def settle(attempt_id, result)
      with_request do |request, record|
        attempt = request.attempts.find(attempt_id)
        evidence = result.evidence || {}
        if %w[expired discarded].include?(attempt.disposition)
          attempt.update!(evidence: evidence, issues: attempt.issues.merge("late_result" => result.issues))
          next
        end
        next if attempt.finished_at

        attempt.update!(finished_at: Time.current, issues: result.issues, evidence: evidence)
        unless current?(request, record)
          attempt.update!(disposition: "discarded")
          next
        end

        if result.status == :complete && valid_completion?(record, result.classification)
          apply!(request, record, attempt, result.classification)
        elsif result.retryable && attempt.number < MAX_ATTEMPTS
          retry_at = Time.current + [RETRY_DELAY.to_i, result.retry_after_seconds.to_i].max
          attempt.update!(disposition: "retry")
          request.update!(available_at: retry_at)
          CompleteRequestJob.schedule(request.id, at: retry_at)
        else
          reason = result.issues.values.first || :catalog_changed
          attempt.update!(disposition: "review", issues: result.issues.presence || { provider: reason })
          review!(request, record, reason.to_s, attempt)
        end
      end
    end

    def valid_completion?(record, classification)
      category, priority = classification.values_at(:category, :priority)
      Catalog.category_active?(record.brand, category) && Catalog::PRIORITIES.key?(priority) &&
        (record.category.nil? || record.category == category) &&
        (record.priority.nil? || record.priority == priority)
    end

    def apply!(request, record, attempt, classification)
      previous = record.classification
      Attendances::ActivateClassifiedCase.call(record, classification)
      request.update!(completed_at: Time.current)
      attempt.update!(disposition: "applied")
      record.audit!("case.classification.completed", actor_type: "system", from_status: "classification_pending",
                    classification: record.classification, previous_classification: previous,
                    classification_version: record.classification_version, attempt_id: attempt.id)
    end

    def review!(request, record, reason, attempt = nil)
      request.update!(completed_at: Time.current)
      record.advance!(status: "classification_review", blocking_reason: reason)
      record.audit!("case.classification.review", actor_type: "system", from_status: "classification_pending",
                    reason: reason, classification_version: request.classification_version, attempt_id: attempt&.id)
    end
  end
end
