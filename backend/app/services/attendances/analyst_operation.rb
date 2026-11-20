module Attendances
  class AnalystOperation
    FIELDS = %w[active_brand_id switch_target_brand_id available].freeze

    def self.update!(user, data)
      Operations::User.transaction do
        # O destino e a origem podem mudar enquanto outra troca está em andamento.
        HumanLocks.all_brands!
        user.lock!
        unless user.role == "analyst" && user.attendant&.kind == "human"
          raise WebhookV1::Error.new(403, "forbidden", "Somente analistas podem alterar a operação.")
        end

        attrs = data.slice("available")
        if data.key?("switch_target_brand_id")
          target = data["switch_target_brand_id"]&.downcase
          if target && !allowed_brand?(user, target)
            raise WebhookV1::Error.new(403, "forbidden", "Marca indisponível para operação.")
          end
          attrs["switch_target_brand_id"] = target == user.active_brand_id ? nil : target
        end
        update_and_audit!(user, attrs, "analyst.operation.updated")
        finish_switch!(user)
        DistributeHumanWorkJob.schedule
      end
    end

    # Chamado com o analista bloqueado. A marca do caso já é tratada pelo chamador.
    def self.release_work!(user, case_brand_id)
      finish_switch!(user)
      operating_brand_id = user.active_brand_id
      DistributeHumanWorkJob.schedule(operating_brand_id) if operating_brand_id && operating_brand_id != case_brand_id
    end

    def self.reconcile_access!(user)
      attrs = {}
      if user.active_brand_id && !allowed_brand?(user, user.active_brand_id)
        attrs[:active_brand_id] = nil
      end
      if user.switch_target_brand_id && !allowed_brand?(user, user.switch_target_brand_id)
        attrs[:switch_target_brand_id] = nil
      end
      update_and_audit!(user, attrs, "analyst.access.revoked") if attrs.any?
      finish_switch!(user)
    end

    def self.finish_switch!(user)
      target = user.switch_target_brand_id
      return if !target || HumanEligibility.portfolio(user.attendant).where(status: "human_active").exists?

      if allowed_brand?(user, target)
        update_and_audit!(user, { active_brand_id: target, switch_target_brand_id: nil }, "analyst.brand.switched")
      else
        update_and_audit!(user, { switch_target_brand_id: nil }, "analyst.brand.switch_cancelled")
      end
    end
    private_class_method :finish_switch!

    def self.allowed_brand?(user, id)
      Visibility.new(user).queues.where(active: true, brand_id: id).exists?
    end
    private_class_method :allowed_brand?

    def self.update_and_audit!(user, attrs, event)
      before = user.attributes.slice(*FIELDS)
      user.update!(attrs)
      after = user.attributes.slice(*FIELDS)
      return if before == after

      Operations::AnalystOperationAudit.create!(user: user, event_type: event, changeset: { before: before, after: after })
    end
    private_class_method :update_and_audit!
  end
end
