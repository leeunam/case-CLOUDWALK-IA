module Webhooks
  module V1
    class EventsController < ApplicationController
      rescue_from WebhookV1::Error do |error|
        data = { code: error.code, message: error.message }
        data[:details] = error.details if error.details
        render json: { error: data }, status: error.status
      end

      rescue_from ActiveRecord::ConnectionNotEstablished, ActiveRecord::ConnectionTimeoutError do
        render json: { error: { code: "unavailable", message: "Persistência temporariamente indisponível." } },
               status: 503
      end

      def channel_message
        channel_id = request.path_parameters.fetch(:channel_id)
        channel = Operations::Channel.find_by(id: channel_id, active: true) if channel_id.match?(WebhookV1::Contract::UUID)
        authenticate!(WebhookV1::Signature.channel_secret(channel)) if channel
        unauthorized! unless channel
        data = WebhookV1::Contract.parse!(request.raw_post, "ChannelMessage")
        receipt = Attendances::ReceiveChannelMessage.new(channel, data, request.raw_post).call
        render json: receipt, status: 202
      end

      def agent_event
        authenticate!(ENV["CLOUDWALK_AGENT_EVENTS_SECRET"])
        data = WebhookV1::Contract.parse!(request.raw_post, "AgentResult")
        receipt = Attendances::ApplyAgentResult.new(data, request.raw_post).call
        render json: receipt
      end

      private

      def authenticate!(secret)
        timestamp = request.get_header("HTTP_X_WEBHOOK_TIMESTAMP")
        signature = request.get_header("HTTP_X_WEBHOOK_SIGNATURE")
        return if WebhookV1::Signature.valid?(secret, request.raw_post, timestamp, signature)

        unauthorized!
      end

      def unauthorized!
        raise WebhookV1::Error.new(401, "unauthenticated", "Assinatura do webhook recusada.")
      end
    end
  end
end
