Rails.application.routes.draw do
  get "up", to: "rails/health#show", as: :rails_health_check

  namespace :api do
    namespace :v1 do
      get "health", to: "health#show"
      resource :session, only: %i[show create destroy]
      patch "session/operation", to: "sessions#update_operation"
      get "case-filters", to: "cases#filters"
      resources :cases, only: %i[index show] do
        get "messages", on: :member
        post "messages", action: :post_message, as: :post_message, on: :member
        post "actions", action: :apply_action, on: :member
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
