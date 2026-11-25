module ApplicationCable
  class Connection < ActionCable::Connection::Base
    def connect
      keys = BrowserAccess::Session::COOKIE_KEYS
      @browser_cookie = keys.values.index_with { |key| request.session[key] }
      reject_unauthorized_connection unless keys.keys.any? { |audience| browser_identity(audience) }
    end

    def browser_identity(audience)
      BrowserAccess::Session.resolve(@browser_cookie, audience)
    end
  end
end
