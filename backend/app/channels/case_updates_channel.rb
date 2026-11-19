class CaseUpdatesChannel < ActionCable::Channel::Base
  def self.stream_name(case_id)
    "case_updates:#{case_id}"
  end

  def self.publish(case_id)
    ActionCable.server.broadcast(stream_name(case_id), { type: "case.updated", case_id: case_id })
  rescue ActiveRecord::ActiveRecordError, PG::Error => error
    Rails.logger.error("Falha ao notificar atualização do atendimento #{case_id}: #{error.class}")
  end

  def subscribed
    @audience = params[:audience]
    raw_id = params[:case_id]
    return reject unless BrowserAccess::Session::COOKIE_KEYS.key?(@audience) &&
      raw_id.is_a?(String) && WebhookV1::Contract::UUID.match?(raw_id)

    @case_id = raw_id.downcase
    return reject unless allowed?

    stream_from(self.class.stream_name(@case_id), coder: ActiveSupport::JSON) { |message| forward_update(message) }
  end

  private

  def allowed?
    BrowserAccess::Session.uncached do
      connection.browser_identity(@audience)&.visible_cases&.exists?(@case_id)
    end
  end

  def forward_update(message)
    if allowed?
      transmit(message)
    else
      stop_all_streams
    end
  end
end
