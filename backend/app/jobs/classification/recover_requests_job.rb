module Classification
  class RecoverRequestsJob < ApplicationJob
    def perform
      Request.due.find_each { |request| CompleteRequestJob.perform_later(request.id) }
    end
  end
end
