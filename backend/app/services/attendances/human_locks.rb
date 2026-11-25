module Attendances
  module HumanLocks
    BRAND_LOCK = "FOR NO KEY UPDATE"

    def self.brand!(brand_id)
      Operations::Brand.lock(BRAND_LOCK).find(brand_id)
    end

    def self.all_brands!
      Operations::Brand.order(:id).lock(BRAND_LOCK).load
    end

    def self.users!(ids)
      Operations::User.where(id: ids).order(:id).lock.to_a
    end
  end
end
