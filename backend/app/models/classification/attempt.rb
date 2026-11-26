module Classification
  class Attempt < ApplicationRecord
    self.table_name = "classification_attempts"

    # O encoder padrão do Rails grava BigDecimal como string. A evidência R1 exige números JSON.
    class Evidence < ActiveRecord::Type::Json
      CODEC = JSON::Coder.new(decimal_class: BigDecimal) do |value|
        if value.is_a?(BigDecimal)
          raise JSON::GeneratorError, "decimal não finito" unless value.finite?
          JSON::Fragment.new(value.to_s)
        else
          value.as_json
        end
      end

      def type = :jsonb

      def serialize(value)
        CODEC.dump(value) unless value.nil?
      end

      def deserialize(value)
        value.is_a?(String) ? CODEC.load(value) : value
      end
    end

    attribute :evidence, Evidence.new

    belongs_to :request, class_name: "Classification::Request", foreign_key: :classification_request_id
  end
end
