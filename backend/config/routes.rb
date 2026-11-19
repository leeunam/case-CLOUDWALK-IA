Rails.application.routes.draw do
  get "up", to: "rails/health#show", as: :rails_health_check

  namespace :api do
    namespace :v1 do
      get "health", to: "health#show"
      resource :session, only: %i[show create destroy]
      get "case-filters", to: "cases#filters"
      resources :cases, only: %i[index show] do
        get "messages", on: :member
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
