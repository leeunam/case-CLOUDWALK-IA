require "digest"

module BrowserAccess
  class SendSimulatorMessage
    def initialize(identity:, channel_id:, key:, data:)
      @identity = identity
      @channel_id = channel_id
      @key = key.to_s
      @data = data
    end

    def call
      if @key.blank? || @key.length > 128
        raise WebhookV1::Error.new(422, "invalid_idempotency_key", "Informe uma chave de idempotência de até 128 caracteres.")
      end

      channel = @identity.simulator_channels.find(@channel_id)
      event_id = Digest::SHA256.hexdigest([@identity.id, channel.id, @key].to_json)
      conversation_id = @data["external_conversation_id"] || "simulator-#{event_id}"
      if @data.key?("external_conversation_id")
        channel.conversations.find_by!(external_conversation_id: conversation_id, simulator_session_id: @identity.id)
      end

      channel_data = @data.merge("source_event_id" => "simulator-#{event_id}", "external_conversation_id" => conversation_id,
                                 "external_customer_id" => @identity.id)
      receipt = Attendances::ReceiveChannelMessage.new(channel, channel_data, JSON.generate(channel_data),
        simulator_session_id: @identity.id, idempotency_body: JSON.generate(@data.sort.to_h)).call
      receipt.merge(channel_id: channel.id, external_conversation_id: conversation_id)
    end
  end
end
