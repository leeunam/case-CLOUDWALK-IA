module Attendances
  class DistributeHumanWork
    PRIORITY = %w[urgent advanced intermediate basic].each_with_index.to_h.freeze
    QUEUED = %w[waiting_human waiting_resumption].freeze

    def initialize(brand_id)
      @brand_id = brand_id
      @cases = SupportCase.where(brand_id: brand_id)
    end

    def call
      @cases.where(status: SupportCase::PORTFOLIO_STATUSES).where.not(assignee_id: nil)
            .includes(assignee: :user).find_each do |record|
        owner = record.assignee&.user
        reconcile(record.id) if owner && !RevokeQueueAccess.allowed?(owner, record)
      end
      pending_ids.each { |id| assign_pending(id) }
    end

    def assign_pending(id)
      SupportCase.transaction do
        HumanLocks.brand!(@brand_id)
        snapshot = @cases.find(id)
        next unless QUEUED.include?(snapshot.status)

        users = if snapshot.status == "waiting_resumption"
          HumanLocks.users!([snapshot.assignee&.user_id])
        else
          ids = Operations::User.where(role: "analyst", active_brand_id: @brand_id, available: true).select(:id)
          HumanLocks.users!(ids)
        end
        record = @cases.lock.find(id)
        next unless record.status == snapshot.status

        candidates = users.map { |user| HumanEligibility.new(user) }
        if record.status == "waiting_resumption"
          candidate = candidates.first
          reason = candidate ? candidate.block_reason(record) : "no_responsible_analyst"
        else
          outcomes = candidates.group_by { |entry| entry.block_reason(record) }
          candidate = outcomes.fetch(nil, []).min_by(&:rank)
          reason = outcomes.keys.one? ? outcomes.keys.first : "no_eligible_analyst" unless candidate
        end
        if reason
          mark_blocked(record, reason)
        else
          activate(record, candidate)
        end
      end
    end

    private

    def pending_ids
      cutoff = 15.minutes.ago
      entries = @cases.where(status: QUEUED).pluck(:id, :status, :priority, :human_queue_since, :created_at)
      entries.sort_by do |id, status, priority, queued_at, created_at|
        since = queued_at || created_at
        rank = PRIORITY.fetch(priority, PRIORITY.size)
        resumption = status == "waiting_resumption" ? 0 : 1
        since <= cutoff ? [0, since, rank, resumption, id] : [1, rank, since, resumption, id]
      end.map(&:first)
    end

    def activate(record, candidate)
      previous = record.status
      resuming = previous == "waiting_resumption"
      record.advance!(status: "human_active", assignee: candidate.attendant, human_queue_since: nil,
                      blocking_reason: nil, assignment_generation: record.assignment_generation + (resuming ? 0 : 1))
      candidate.user.update!(last_human_assignment_at: Time.current) unless resuming
      record.audit!(resuming ? "case.human.resumed" : "case.human.assigned",
                    actor_type: "system", from_status: previous, assignee_id: candidate.attendant.id,
                    queue_id: record.queue_id, profile_version: candidate.profile.version)
    end

    def mark_blocked(record, reason)
      return if record.blocking_reason == reason

      record.advance!(blocking_reason: reason)
      record.audit!("case.human.blocked", actor_type: "system", reason: reason, queue_id: record.queue_id)
    end

    def reconcile(id)
      SupportCase.transaction do
        HumanLocks.brand!(@brand_id)
        owner = HumanLocks.users!([@cases.find(id).assignee&.user_id]).first
        record = @cases.lock.find(id)
        RevokeQueueAccess.call(record, owner) if owner
      end
    end
  end
end
