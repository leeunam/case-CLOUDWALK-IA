module Classification
  class RecoverRequestsJob < ApplicationJob
    def perform
      Request.due.find_each { |request| CompleteRequestJob.set(queue: request.job_queue).perform_later(request.id) }
    end
  end
end
