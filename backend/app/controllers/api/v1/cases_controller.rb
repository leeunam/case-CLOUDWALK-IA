module Api
  module V1
    class CasesController < BrowserController
      before_action :require_user!

      FILTERS = %w[brand_id queue_id status integration_status category priority assignee].freeze
      UUID = WebhookV1::Contract::UUID

      def filters
        render json: {
          brands: visibility.brands.order(:name, :id).as_json(only: %i[id name]),
          queues: visibility.queues.order(:name, :id).as_json(only: %i[id brand_id name])
        }
      end

      def index
        limit = bounded_integer("limit", default: 25, range: 1..100)
        filters = request.query_parameters.slice(*FILTERS)
        relation = filtered_cases(filters)
        if (cursor = cursor_position(filters))
          relation = relation.where("(created_at, id) < (?, ?)", Time.iso8601(cursor.fetch("created_at")), cursor.fetch("id"))
        end

        rows = relation.includes(:assignee).order(created_at: :desc, id: :desc).limit(limit + 1).to_a
        items = rows.first(limit)
        next_cursor = encode_cursor(items.last, filters) if rows.size > limit
        render json: { items: items.map(&:contract_data), next_cursor: next_cursor }
      end

      def show
        render json: visible_case.contract_data
      end

      def messages
        after = bounded_integer("after_sequence", default: 0, range: 0..)
        limit = bounded_integer("limit", default: 25, range: 1..100)
        rows = visible_case.messages.where("sequence > ?", [after, 2**31 - 1].min).order(:sequence).limit(limit + 1).to_a
        items = rows.first(limit)
        render json: { items: items.map(&:contract_data), next_after_sequence: rows.size > limit ? items.last.sequence : nil }
      end

      def post_message
        render json: apply_command("message", "NewCaseMessage"), status: :created
      end

      def apply_action
        render json: apply_command("action", "CaseAction")
      end

      def correct_classification
        render json: apply_command("classification", "CaseClassificationCorrection")
      end

      def audit
        record = visible_case
        unless current_user.role == "supervisor"
          raise WebhookV1::Error.new(403, "forbidden", "A auditoria exige acesso de supervisão.")
        end

        limit = bounded_integer("limit", default: 25, range: 1..100)
        filters = { "audit_case_id" => record.id }
        relation = record.audits
        if (cursor = cursor_position(filters))
          relation = relation.where("(created_at, id) < (?, ?)", Time.iso8601(cursor.fetch("created_at")), cursor.fetch("id"))
        end

        rows = relation.order(created_at: :desc, id: :desc).limit(limit + 1).to_a
        items = rows.first(limit)
        next_cursor = encode_cursor(items.last, filters) if rows.size > limit
        render json: { items: items.map(&:contract_data), next_cursor: next_cursor }
      end

      private

      def apply_command(operation, definition)
        data = WebhookV1::Contract.parse!(request.raw_post, definition)
        Attendances::ApplyCaseCommand.new(user: current_user, case_id: request.path_parameters.fetch(:id),
                                          operation: operation, key: request.headers["Idempotency-Key"], data: data).call
      end

      def visibility
        @visibility ||= Attendances::Visibility.new(current_user)
      end

      def visible_case
        visibility.cases.find(request.path_parameters.fetch(:id))
      end

      def filtered_cases(filters)
        relation = visibility.cases
        filters.each do |key, value|
          allowed = case key
          when "brand_id", "queue_id" then UUID
          when "status" then Attendances::SupportCase::STATUSES
          when "integration_status" then Attendances::SupportCase::INTEGRATION_STATUSES
          when "category" then /\A[a-z][a-z0-9_]*\z/
          when "priority" then Attendances::ReceiveChannelMessage::PRIORITIES
          when "assignee" then %w[me unassigned]
          end
          valid = allowed.is_a?(Regexp) ? value.is_a?(String) && allowed.match?(value) : allowed.include?(value)
          invalid_query!(key) unless valid

          if key == "assignee"
            if value == "me"
              attendant = Operations::Attendant.find_by(user: current_user)
              relation = attendant ? relation.where(assignee_id: attendant.id) : relation.none
            else
              relation = relation.where(assignee_id: nil)
            end
          else
            relation = relation.where(key => value)
          end
        end
        relation
      end

      def bounded_integer(key, default:, range:)
        raw = request.query_parameters.fetch(key, default.to_s)
        value = Integer(raw, 10, exception: false) if raw.is_a?(String) && raw.match?(/\A[0-9]+\z/)
        invalid_query!(key) unless value && range.cover?(value)
        value
      end

      def invalid_query!(key)
        raise WebhookV1::Error.new(422, "invalid_query", "Parâmetro inválido: #{key}.")
      end

      def cursor_position(filters)
        raw = request.query_parameters["cursor"]
        return if raw.nil?

        invalid_query!("cursor") unless raw.is_a?(String) && raw.present?
        cursor = cursor_verifier.verified(raw, purpose: current_user.id)
        invalid_query!("cursor") unless cursor && cursor["filters"] == filters
        cursor
      end

      def encode_cursor(record, filters)
        cursor_verifier.generate({ "created_at" => record.created_at.iso8601(6), "id" => record.id,
                                  "filters" => filters }, purpose: current_user.id)
      end

      def cursor_verifier
        Rails.application.message_verifier("attendances-case-list")
      end
    end
  end
end
