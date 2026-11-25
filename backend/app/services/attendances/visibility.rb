module Attendances
  class Visibility
    def initialize(user)
      @user = user
    end

    def queues
      if @user.role == "supervisor"
        return Operations::SupportQueue.where(brand_id: supervised_brand_ids)
      end

      subjects = Operations::BrandTeam.where(team_id: @user.team_memberships.select(:team_id))
      links = Operations::QueueTeam.where(brand_team_id: subjects.select(:id))
      Operations::SupportQueue.where(id: links.select(:support_queue_id))
    end

    def brands
      ids = @user.role == "supervisor" ? supervised_brand_ids : queues.select(:brand_id)
      Operations::Brand.where(id: ids)
    end

    def cases
      SupportCase.where(queue_id: queues.select(:id))
    end

    private

    def supervised_brand_ids
      Operations::SupervisorBrand.where(user: @user).select(:brand_id)
    end
  end
end
