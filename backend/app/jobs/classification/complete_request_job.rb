module Classification
  class CompleteRequestJob < ApplicationJob
    def self.schedule(request, at: nil)
      ActiveRecord.after_all_transactions_commit do
        set(queue: request.job_queue, wait_until: at).perform_later(request.id)
      rescue ActiveJob::EnqueueError, SolidQueue::Job::EnqueueError => error
        Rails.logger.error("Não foi possível agendar classificação #{request.id}: #{error.class}")
      end
    end

    def perform(request_id)
      CompleteRequest.new(request_id).call
    end
  end
end
