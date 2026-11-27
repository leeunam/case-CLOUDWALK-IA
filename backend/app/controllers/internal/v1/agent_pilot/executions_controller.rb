module Internal
  module V1
    module AgentPilot
      class ExecutionsController
        include AgentIntegration::Pilot
        MAX_BYTES = 128.kilobytes

        # O roteamento chama Rack diretamente para preservar os bytes assinados
        # e impedir que o parser e o log de parâmetros do Rails vejam o corpo.
        def self.call(env)
          request = ActionDispatch::Request.new(env)
          bytes = request.body.read(MAX_BYTES + 1) || "".b
          raise Error, "too_large" if bytes.bytesize > MAX_BYTES

          Authentication.verify!(request, bytes)
          id, operation = request.path_parameters.values_at(:request_event_id, :operation)
          unless Contract::UUID.match?(id) && request.path == "/internal/v1/e01/executions/#{id}/#{operation}" &&
                 request.query_string.empty? && request.get_header("REQUEST_URI").to_s.exclude?("?") &&
                 [nil, "identity"].include?(request.get_header("HTTP_CONTENT_ENCODING")) &&
                 request.get_header("CONTENT_ENCODING").blank?
            raise Error, "invalid_body"
          end

          body = Contract.parse_operation!(operation, bytes)
          response(200, Ledger.new(id, body, bytes).call(operation))
        rescue Error => error
          response(error.status, { error: error.message })
        rescue ActiveRecord::ConnectionNotEstablished, ActiveRecord::ConnectionTimeoutError
          [503, { "cache-control" => "no-store" }, []]
        end

        def self.response(status, data)
          [status, { "content-type" => "application/json; charset=utf-8", "cache-control" => "no-store" },
           [JSON.generate(data)]]
        end
      end
    end
  end
end
