module AgentIntegration
  module E01
    class Ledger
      RESERVED_LEASE = 10.seconds
      STARTED_LEASE = 40.seconds
      ROUND_MARGIN = 5.seconds
      TERMINAL_STATES = %w[failed discarded unknown published].freeze

      def self.sweep_once
        id = Execution.expirable.where(lease_expires_at: ..Time.current).pick(:request_event_id)
        return false unless id

        Pilot.transaction do
          Pilot.lock_current!
          round = Round.new(id)
          execution = Execution.lock.find_by!(request_event_id: id)
          expire!(round, execution, Time.current)
        end
      end

      def self.expire!(round, execution, now)
        return false unless execution && execution.lease_expires_at <= now

        case execution.state
        when "reserved"
          execution.update!(state: "expired")
        when "started"
          mark_unknown!(round, execution, "dispatch_uncertain", now)
        else
          return false
        end
        true
      end

      def self.mark_unknown!(round, execution, reason, now)
        execution.update!(state: "unknown", reason: reason)
        round.record!(reason, now, failure: true)
      end

      def initialize(request_event_id, body, bytes)
        @request_event_id = request_event_id
        @body = body
        @bytes = bytes
      end

      def call(operation)
        self.class.sweep_once if operation == "claim"
        response = Pilot.transaction do
          @pilot = Pilot.lock_current!
          @round = Round.new(@request_event_id)
          @execution = Execution.lock.find_by(request_event_id: @request_event_id)
          sha256 = @body["request_sha256"] || @execution&.request_sha256 || @round.body_sha256
          @round.verify_origin!(sha256)
          if @execution && @execution.request_sha256 != sha256
            raise Error, "request_mismatch"
          end

          @now = Time.current
          self.class.expire!(@round, @execution, @now)
          case operation
          when "claim" then claim
          when "start" then start
          when "complete" then complete
          when "unknown" then unknown
          when "published" then published
          end
        rescue Error => error
          # A expiração e a sinalização de falha precisam sobreviver à resposta HTTP.
          error
        end
        raise response if response.is_a?(Error)

        response
      end

      private

      def claim
        case @execution&.state
        when "started" then return already_started
        when "result_saved" then return saved_result
        when *TERMINAL_STATES then return { state: @execution.state }
        end

        @round.dispatchable!(@now)
        if @execution&.state == "reserved"
          raise Error, "busy" unless @execution.owner_id == @body.fetch("owner_id")

          return reserved
        end

        deadline = lease_deadline!(RESERVED_LEASE)
        case Execution.holding_slot.pick(:state)
        when "unknown" then reject_turn!("pilot_paused")
        when "reserved", "started" then raise Error, "busy"
        end
        snapshot = require_preflight!
        rejects_budget!(snapshot.reserve)

        attributes = { state: "reserved", owner_id: @body.fetch("owner_id"), lease_token: SecureRandom.uuid,
                       lease_expires_at: deadline }
        if @execution
          @execution.update!(**attributes)
        else
          @execution = Execution.create!(**attributes, request_event_id: @request_event_id,
                                         request_sha256: @body.fetch("request_sha256"), snapshot: snapshot.data,
                                         reserved_usd: snapshot.reserve)
        end
        reserved
      end

      def start
        verify_lease!
        return already_started if @execution.state == "started"
        raise Error, "invalid_state" unless @execution.state == "reserved"

        @round.dispatchable!(@now)
        deadline = lease_deadline!(STARTED_LEASE)
        require_preflight!
        rejects_budget!(@execution.reserved_usd)

        @execution.update!(state: "started", started_at: @now, lease_expires_at: deadline)
        @pilot.update!(dispatch_count: @pilot.dispatch_count + 1)
        { state: "started", dispatch: true, lease_expires_at: deadline.iso8601(6) }
      end

      def complete
        digest = Digest::SHA256.hexdigest(@bytes)
        if @execution&.complete_sha256
          raise Error, "result_mismatch" unless @execution.complete_sha256 == digest

          return completion_result
        end

        verify_started!
        usage = @body.fetch("usage")
        snapshot = Preflight.new(@execution.snapshot)
        cost = snapshot.cost!(usage)
        raise Error, "invalid_body" if cost > @execution.reserved_usd

        attributes = { usage: usage, cost_usd: cost, complete_sha256: digest }
        proposed = Result.new(@body, @round.request_data, snapshot) if @body.fetch("outcome") == "result"
        attributes[:result_metadata] = proposed.metadata if proposed
        if !@round.current?(@now)
          attributes.merge!(state: "discarded", reason: "turn_stale")
          @round.record!("turn_stale", @now)
        elsif proposed
          attributes.merge!(state: "result_saved", result_bytes: proposed.bytes, result_sha256: proposed.sha256)
        else
          reason = @body.fetch("reason")
          attributes.merge!(state: "failed", reason: reason)
          @round.record!(reason, @now, failure: true)
        end
        @execution.update!(**attributes)
        @pilot.update!(spent_usd: @pilot.spent_usd + cost)
        completion_result
      end

      def unknown
        verify_started!
        self.class.mark_unknown!(@round, @execution, @body.fetch("reason"), @now)
        { state: "unknown" }
      end

      def published
        raise Error, "invalid_state" unless %w[result_saved published].include?(@execution&.state)
        raise Error, "result_mismatch" unless @execution.result_sha256 == @body.fetch("result_sha256")

        @execution.update!(state: "published", published_at: @now) unless @execution.state == "published"
        { state: "published" }
      end

      def verify_lease!
        unless @execution && @execution.lease_expires_at > @now &&
               @execution.owner_id == @body.fetch("owner_id") && @execution.lease_token == @body.fetch("lease_token")
          raise Error, "lease_lost"
        end
      end

      def verify_started!
        verify_lease!
        raise Error, "invalid_state" unless @execution.state == "started"
      end

      def lease_deadline!(duration)
        deadline = [@now + duration, @round.turn.result_due_at - ROUND_MARGIN].min
        raise Error, "turn_stale" if deadline <= @now

        deadline
      end

      def require_preflight!
        snapshot = Preflight.load!
        if @execution && @execution.snapshot != snapshot.data
          raise Error, "preflight_missing"
        end

        snapshot
      rescue Error => error
        reject_turn!(error.message)
      end

      def rejects_budget!(amount)
        reject_turn!("budget_exhausted") unless @pilot.allows?(amount)
      end

      def reject_turn!(reason)
        @execution.update!(state: "expired") if @execution&.state == "reserved"
        @round.record!(reason, @now, failure: true)
        raise Error, reason
      end

      def reserved
        amount = @execution.reserved_usd
        whole, fraction = amount.to_s("F").split(".")
        { state: "reserved", lease_token: @execution.lease_token, lease_expires_at: @execution.lease_expires_at.iso8601(6),
          currency: "USD", reserved_usd: "#{whole}.#{fraction.ljust(12, '0')}" }
      end

      def already_started
        { state: "started", dispatch: false }
      end

      def saved_result
        { state: "result_saved", result_b64: Base64.strict_encode64(@execution.result_bytes), result_sha256: @execution.result_sha256 }
      end

      def completion_result
        return saved_result if %w[result_saved published].include?(@execution.state)

        { state: @execution.state }
      end
    end
  end
end
