require "net/http"
require "timeout"

module AgentIntegration
  class DeliverOutbox
    LEASE = 15.seconds
    RESULT_TIMEOUT = 60.seconds
    RETRIES = [1.second, 3.seconds].freeze

    def initialize(url: ENV.fetch("CLOUDWALK_AGENT_REQUEST_URL"), secret: ENV.fetch("CLOUDWALK_AGENT_REQUESTS_SECRET"))
      @url = URI(url)
      @secret = secret
    end

    def run_once
      expire_turns
      entry = claim
      return false unless entry

      result = entry.agent_turn.completed_at ? "result_already_received" : publish(entry.body)
      record_result(entry, result)
      true
    end

    private

    def claim
      AgentOutbox.transaction do
        now = Time.current
        entry = AgentOutbox.where(published_at: nil, failed_at: nil).where("next_attempt_at <= ?", now)
                           .order(:next_attempt_at, :id).lock("FOR UPDATE SKIP LOCKED").first
        if entry
          entry.update!(claim_token: SecureRandom.uuid, next_attempt_at: now + LEASE,
                        attempts: entry.attempts + 1)
        end
        entry
      end
    end

    def publish(body)
      request = Net::HTTP::Post.new(@url)
      request["Content-Type"] = "application/json"
      request.body = body
      WebhookV1::Signature.headers(@secret, body).each { |key, value| request[key] = value }
      status = Timeout.timeout(2) do
        Net::HTTP.start(@url.host, @url.port, use_ssl: @url.scheme == "https",
                        open_timeout: 2, read_timeout: 2, write_timeout: 2) do |http|
          http.request(request).code
        end
      end
      status == "202" ? "published" : "bridge_http_#{status}"
    rescue Timeout::Error, SocketError, IOError, SystemCallError, OpenSSL::SSL::SSLError => error
      "bridge_#{error.class.name}"
    end

    def record_result(claimed, result)
      turn = claimed.agent_turn
      support_case = turn.support_case
      support_case.with_lock do
        turn.lock!
        entry = AgentOutbox.lock.find(claimed.id)
        next if entry.claim_token != claimed.claim_token

        now = Time.current
        if result == "published" || turn.result_event_id
          confirm_publication(support_case, turn, entry, now)
        elsif turn.completed_at || entry.attempts > RETRIES.size || result.match?(/\Abridge_http_4(?!29)/)
          entry.update!(failed_at: now, claim_token: nil)
          if turn.completed_at.nil?
            support_case.advance!(integration_status: "failed", blocking_reason: result)
            support_case.audit!("agent.delivery.failed", actor_type: "system", reason: result,
                                event_id: entry.event_id, turn_id: turn.id, attempts: entry.attempts)
          end
        else
          entry.update!(next_attempt_at: now + RETRIES.fetch(entry.attempts - 1), claim_token: nil)
        end
      end
    end

    def confirm_publication(support_case, turn, entry, now)
      entry.update!(published_at: now, claim_token: nil)
      if turn.completed_at.nil?
        turn.update!(result_due_at: now + RESULT_TIMEOUT)
        support_case.advance!(integration_status: "awaiting_result")
      end
      support_case.audit!("agent.delivery.confirmed", actor_type: "system",
                          event_id: entry.event_id, turn_id: turn.id, attempts: entry.attempts)
    end

    def expire_turns
      AgentTurn.in_flight.where(result_due_at: ..Time.current).limit(50).each do |turn|
        support_case = turn.support_case
        support_case.with_lock do
          turn.lock!
          now = Time.current
          next if turn.completed_at || !turn.result_due_at || turn.result_due_at > now

          turn.update!(completed_at: now)
          support_case.advance!(integration_status: "failed", blocking_reason: "agent_result_timeout")
          support_case.audit!("agent.result.expired", actor_type: "system", reason: "agent_result_timeout",
                              event_id: turn.request_event_id, turn_id: turn.id)
        end
      end
    end
  end
end
