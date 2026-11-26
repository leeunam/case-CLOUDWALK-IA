Rails.application.routes.draw do
  get "up", to: "rails/health#show", as: :rails_health_check

  post "internal/v1/e01/executions/:request_event_id/:operation",
       to: Internal::V1::E01::ExecutionsController,
       constraints: { operation: /claim|start|complete|unknown|published/ }, format: false

  namespace :api do
    namespace :v1 do
      get "health", to: "health#show"
      resource :session, only: %i[show create destroy]
      patch "session/operation", to: "sessions#update_operation"
      get "case-filters", to: "cases#filters"
      scope controller: :configuration do
        get "brands", action: :brands
        put "brands/:brand_id", action: :update_brand
        get "teams", action: :teams
        get "team-members", action: :team_members
        get "analysts", action: :analysts
        get "analysts/:analyst_id/capacity-profile", action: :capacity_profile
        post "analysts/:analyst_id/capacity-profile", action: :create_capacity_profile
        put "analysts/:analyst_id/capacity-profile", action: :update_capacity_profile
        post "teams", action: :create_team
        put "teams/:id", action: :update_team
        scope "brands/:brand_id" do
          get "queues", action: :queues
          post "queues", action: :create_queue
          get "queues/:id/analysts", action: :queue_analysts
          put "queues/:id", action: :update_queue
          get "routing-rules", action: :routing_rules
          post "routing-rules", action: :create_routing_rule
          put "routing-rules/:id", action: :update_routing_rule
          get "configuration-audit", action: :configuration_audit
          get "catalog", action: :catalog
          put "catalog", action: :update_catalog
        end
      end
      get "channels", to: "channels#index"
      post "simulator/session", to: "simulator#start_session"
      get "simulator/cases", to: "simulator#index"
      get "simulator/cases/:id", to: "simulator#show"
      get "simulator/cases/:id/messages", to: "simulator#messages"
      post "simulator/channels/:channel_id/messages", to: "simulator#send_message"
      resources :cases, only: %i[index show] do
        get "messages", on: :member
        post "messages", action: :post_message, as: :post_message, on: :member
        post "actions", action: :apply_action, on: :member
        post "classification", action: :correct_classification, on: :member
        get "audit", on: :member
      end
    end
  end

  namespace :webhooks do
    namespace :v1 do
      post "channels/:channel_id/messages", to: "events#channel_message"
      post "agent/events", to: "events#agent_event"
    end
  end
end
