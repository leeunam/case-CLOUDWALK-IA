module Api
  module V1
    class SimulatorController < BrowserController
      before_action :require_simulator!, except: :start_session

      rescue_from ActiveRecord::ConnectionNotEstablished, ActiveRecord::ConnectionTimeoutError do
        render json: { error: { code: "unavailable", message: "Persistência temporariamente indisponível." } }, status: 503
      end

      def start_session
        identity = simulator_identity
        identity ||= start_browser_identity!("simulator")
        render json: simulator_session_data(identity), status: :created
      end

      def index
        page = paginated(simulator_identity.visible_cases.includes(:channel_conversation),
                         order: [:created_at, :id], scope: ["simulator-cases", simulator_identity.id])
        render json: page.merge(items: page.fetch(:items).map { |record| simulator_case_data(record) })
      end

      def show
        render json: simulator_case_data(visible_case)
      end

      def messages
        render json: messages_page(visible_case.messages.where(author_type: %w[customer ai human]))
      end

      def send_message
        verify_simulator_identity!
        data = WebhookV1::Contract.parse!(request.raw_post, "SimulatorMessage")
        receipt = BrowserAccess::SendSimulatorMessage.new(identity: simulator_identity,
          channel_id: request.path_parameters.fetch(:channel_id), key: request.headers["Idempotency-Key"], data: data).call
        render json: receipt, status: :accepted
      end

      private

      def verify_simulator_identity!
        expected = request.headers["X-Simulator-Session-Id"]
        return if expected.nil?
        unless WebhookV1::Contract::UUID.match?(expected)
          raise WebhookV1::Error.new(422, "invalid_simulator_session_id", "Informe um UUID em X-Simulator-Session-Id.")
        end
        return if expected.casecmp?(simulator_identity.id)

        raise WebhookV1::Error.new(409, "simulator_session_changed",
          "A sessão do simulador mudou desde o início deste envio.")
      end

      def visible_case
        simulator_identity.visible_cases.find(request.path_parameters.fetch(:id))
      end

      def simulator_case_data(record)
        {
          id: record.id, previous_case_id: record.previous_case_id, status: record.status,
          updated_at: record.updated_at.iso8601(6), channel_id: record.channel_id,
          external_conversation_id: record.channel_conversation.external_conversation_id
        }
      end
    end
  end
end
