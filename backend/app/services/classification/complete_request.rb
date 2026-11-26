module Classification
  class CompleteRequest
    MAX_ATTEMPTS = 2
    LEASE = 30.seconds
    RETRY_DELAY = 1.second

    def initialize(request_id, classifier: nil)
      @request_id = request_id
      @classifier = classifier
    end

    def call
      claim = claim_attempt
      return unless claim

      attempt, text = claim
      snapshot = attempt.snapshot
      result = if @classifier
        @classifier.call(categories: snapshot.dig("catalog", "category"), text: text, **snapshot.fetch("received").symbolize_keys)
      else
        ConfiguredProvider.call(attempt, text)
      end
      settle(attempt.id, result)
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
          last_issue = "invalid_response" unless %w[worker_lease_expired busy not_ready timeout network_error http_error].include?(last_issue)
          review!(request, record, last_issue, last)
          next
        end

        message = record.messages.where(author_type: "customer").order(:sequence).first
        unless message
          review!(request, record, "missing_classification_text")
          next
        end

        ConfiguredProvider.pin_legacy!(request)
        snapshot = capture(request, record, message)
        lease = LEASE.from_now
        attempt = request.attempts.create!(number: (last&.number || 0) + 1, snapshot: snapshot, lease_expires_at: lease)
        request.update!(available_at: lease)
        [attempt, message.text]
      end
    end

    def capture(request, record, message)
      catalog = Catalog.snapshot(record.brand)
      snapshot = {
        "provider" => request.provider, "provider_mode" => request.provider_mode, "message_id" => message.id,
        "catalog" => catalog, "catalog_sha256" => SetfitContract.catalog_sha256(catalog),
        "catalog_version" => record.brand.catalog_version, "classification_version" => record.classification_version,
        "received" => record.slice(:category, :priority), "sources" => record.slice(:category_source, :priority_source)
      }
      if request.provider == "setfit"
        snapshot["identities"] = begin
          SetfitContract.current.identities
        rescue SetfitContract::Unavailable
          {}
        end
      end
      snapshot
    end

    def settle(attempt_id, result)
      with_request do |request, record|
        attempt = request.attempts.find(attempt_id)
        evidence = result.evidence || {}
        if %w[expired discarded].include?(attempt.disposition)
          unless attempt.issues.key?("late_result")
            observed = attempt.evidence.empty? ? evidence : attempt.evidence.merge("late_result" => evidence)
            attempt.update!(evidence: observed, issues: attempt.issues.merge("late_result" => result.issues))
          end
          next
        end
        next if attempt.finished_at

        attempt.update!(finished_at: Time.current, issues: result.issues, evidence: evidence)
        unless current?(request, record) && request.attempts.maximum(:number) == attempt.number
          attempt.update!(disposition: "discarded")
          next
        end

        invalidated = invalidated_reason(request, record, attempt)
        if invalidated
          attempt.update!(disposition: "discarded", issues: result.issues.merge(provider: invalidated))
          review!(request, record, invalidated, attempt)
        elsif result.status == :complete && valid_completion?(request, record, result.classification)
          apply!(request, record, attempt, result.classification)
        elsif result.retryable && attempt.number < MAX_ATTEMPTS
          retry_at = Time.current + [RETRY_DELAY.to_i, result.retry_after_seconds.to_i].max
          attempt.update!(disposition: "retry")
          request.update!(available_at: retry_at)
          CompleteRequestJob.schedule(request, at: retry_at)
        else
          reason = result.issues.values.first || :invalid_response
          attempt.update!(disposition: "review", issues: result.issues.presence || { provider: reason })
          review!(request, record, reason.to_s, attempt)
        end
      end
    end

    def invalidated_reason(request, record, attempt)
      return "worker_lease_expired" if [request.available_at, attempt.lease_expires_at].min <= Time.current

      snapshot = attempt.snapshot
      return "invalid_input" unless record.classification_version == snapshot.fetch("classification_version") &&
        record.slice(:category, :priority) == snapshot.fetch("received") &&
        record.slice(:category_source, :priority_source) == snapshot.fetch("sources")

      catalog = Catalog.snapshot(record.brand)
      "catalog_changed" unless record.brand.catalog_version == snapshot.fetch("catalog_version") &&
        SetfitContract.catalog_sha256(catalog) == snapshot.fetch("catalog_sha256")
    end

    def valid_completion?(request, record, classification)
      return false unless classification.is_a?(Hash) && classification.keys.sort == %i[category category_source priority priority_source]
      return false unless Catalog.category_active?(record.brand, classification[:category]) && Catalog::PRIORITIES.key?(classification[:priority])

      %i[category priority].all? do |field|
        received = record[field]
        absent = received.nil? || received == ""
        (absent || received == classification[field]) && classification[:"#{field}_source"] == (absent ? request.provider : "channel")
      end
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
