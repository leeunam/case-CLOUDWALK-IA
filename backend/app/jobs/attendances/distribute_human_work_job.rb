module Attendances
  class DistributeHumanWorkJob < ApplicationJob
    def self.schedule(brand_id = nil)
      ActiveRecord.after_all_transactions_commit do
        perform_later(brand_id)
      rescue ActiveJob::EnqueueError, SolidQueue::Job::EnqueueError => error
        Rails.logger.error("Não foi possível sinalizar distribuição humana: #{error.class}")
      end
    end

    def perform(brand_id = nil)
      brands = brand_id ? Operations::Brand.where(id: brand_id) : Operations::Brand.all
      brands.find_each { |brand| DistributeHumanWork.new(brand.id).call }
    end
  end
end
