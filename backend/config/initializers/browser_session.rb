Rails.application.config.filter_parameters += [:password]
Rails.application.config.session_store :cookie_store, key: "_cloudwalk_session",
                                       httponly: true, same_site: :lax, secure: Rails.env.production?
Rails.application.config.middleware.use ActionDispatch::Cookies
Rails.application.config.middleware.use Rails.application.config.session_store,
                                        Rails.application.config.session_options
