module Attendances
  class HumanEligibility
    attr_reader :user, :attendant, :profile, :active_count

    def self.portfolio(attendant)
      SupportCase.where(assignee: attendant, status: SupportCase::PORTFOLIO_STATUSES)
    end

    def initialize(user)
      @user = user
      @attendant = user.attendant
      @profile = user.capacity_profiles.find_by(active: true)
      @portfolio = attendant ? self.class.portfolio(attendant) : SupportCase.none
      @active = @portfolio.where(status: "human_active").pluck(:id, :priority, :category)
      @active_count = @active.size
    end

    def rank
      last = user.last_human_assignment_at
      [active_count, last ? 1 : 0, last || Time.at(0), user.id]
    end

    def block_reason(record, queue: record.queue, activates: true)
      return "no_human_attendant" unless attendant&.kind == "human" && user.role == "analyst"
      return "queue_access_revoked" unless queue.active? && Visibility.new(user).queues.exists?(queue.id)
      return "brand_switch_pending" if user.switch_target_brand_id
      return "different_operating_brand" unless user.active_brand_id == record.brand_id
      return "analyst_unavailable" unless user.available?
      return "no_active_capacity_profile" unless profile

      owned = record.assignee_id == attendant.id && SupportCase::PORTFOLIO_STATUSES.include?(record.status)
      return "portfolio_limit" if !owned && @portfolio.count >= profile.portfolio_limit

      pairs = @active.reject { |id, _, _| id == record.id }.map { |_, priority, category| [priority, category] }
      pairs << [record.priority, record.category] if activates
      "active_capacity" unless profile.fits?(pairs.tally)
    end
  end
end
