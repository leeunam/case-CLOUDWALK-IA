# Executar com bin/rails runner script/check_outbox.rb.
stop = false
%w[INT TERM].each { |signal| Signal.trap(signal) { stop = true } }

delivery = AgentIntegration::DeliverOutbox.new
until stop
  work_done = Rails.application.executor.wrap { delivery.run_once }
  sleep(0.25) unless work_done
end
