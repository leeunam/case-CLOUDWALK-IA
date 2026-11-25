module Attendances
  module ActivateClassifiedCase
    # Chamado sob bloqueio da marca e do atendimento.
    def self.call(record, classification)
      queue, rule = InitialRouting.choose(record.brand, classification)
      assignee = Operations::Attendant.find_by!(code: "mock", kind: "ai")
      record.advance!(**classification, status: "ai_active", blocking_reason: nil, queue: queue,
                       assignee: assignee, classification_version: record.classification_version + 1)
      InitialRouting.record!(record, rule)
      AgentIntegration::QueueTurn.call(record)
    end
  end
end
