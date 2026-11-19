module Classification
  class CompleteRequestJob < ApplicationJob
    def self.schedule(request_id, at: nil)
      ActiveRecord.after_all_transactions_commit do
        job = at ? set(wait_until: at) : self
        job.perform_later(request_id)
      rescue ActiveJob::EnqueueError, SolidQueue::Job::EnqueueError => error
        Rails.logger.error("Não foi possível agendar classificação #{request_id}: #{error.class}")
      end
    end

    def perform(request_id)
      CompleteRequest.new(request_id).call
    end
  end
end
