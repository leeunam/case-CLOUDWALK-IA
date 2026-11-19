module WebhookV1
  class Error < StandardError
    attr_reader :status, :code, :details

    def initialize(status, code, message, details = nil)
      super(message)
      @status = status
      @code = code
      @details = details
    end
  end
end
