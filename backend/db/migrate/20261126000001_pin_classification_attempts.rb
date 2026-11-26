class PinClassificationAttempts < ActiveRecord::Migration[8.1]
  def change
    add_column :classification_requests, :provider, :string
    add_column :classification_requests, :provider_mode, :string
    add_column :classification_attempts, :snapshot, :jsonb, null: false, default: {}
    add_column :classification_attempts, :lease_expires_at, :datetime
  end
end
