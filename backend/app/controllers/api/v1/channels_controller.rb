module Api
  module V1
    class ChannelsController < BrowserController
      def index
        if simulator_identity
          identity = simulator_identity
          channels = identity.simulator_channels
        else
          require_user!
          identity = staff_identity
          brands = Attendances::Visibility.new(current_user).brands
          channels = Operations::Channel.where(active: true, brand_id: brands.select(:id))
        end

        page = paginated(channels.includes(:brand), order: [:id], scope: ["channels", identity.id])
        items = page.fetch(:items).map do |channel|
          { id: channel.id, brand_id: channel.brand_id, brand_name: channel.brand.name,
            name: channel.name, type: channel.kind }
        end
        render json: page.merge(items: items)
      end
    end
  end
end
