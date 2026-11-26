module Classification
  Result = Data.define(:status, :classification, :issues, :evidence, :retryable, :retry_after_seconds) do
    def self.review(reason, evidence: nil, retryable: false)
      new(status: :review, classification: {}, issues: { provider: reason }, evidence: evidence,
          retryable: retryable, retry_after_seconds: nil)
    end
  end
end
