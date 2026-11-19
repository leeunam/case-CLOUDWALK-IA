require_relative "boot"

require "rails"
require "active_model/railtie"
require "active_job/railtie"
require "active_record/railtie"
require "action_controller/railtie"
require "action_cable/engine"
require "rails/test_unit/railtie"

Bundler.require(*Rails.groups)

module Cloudwalk
  class Application < Rails::Application
    config.load_defaults 8.1
    config.api_only = true
    config.action_cable.mount_path = "/cable"
    config.active_job.queue_adapter = :solid_queue
    config.solid_queue.connects_to = { database: { writing: :queue } }

    config.generators do |generator|
      generator.orm :active_record, primary_key_type: :uuid
    end
  end
end
