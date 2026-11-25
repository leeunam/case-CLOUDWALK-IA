module Classification
  module Catalog
    PRIORITIES = {
      "basic" => "Orientação de rotina, sem operação prejudicada.",
      "intermediate" => "Impacto moderado com operação ainda disponível.",
      "advanced" => "Impacto relevante sem necessidade de ação imediata.",
      "urgent" => "Necessidade de ação imediata, como operação totalmente interrompida."
    }.freeze
    CATEGORY_DESCRIPTIONS = {
      "pix" => "Transferência ou pagamento por Pix, prazo, estorno ou falha.",
      "payouts" => "Repasse, recebimento ou liquidação de valores de vendas.",
      "terminal" => "Instalação, uso ou defeito da maquininha de cartão."
    }.freeze
    CATEGORY_CODE = /\A[a-z][a-z0-9_]*\z/

    def self.category_code?(code)
      code.is_a?(String) && CATEGORY_CODE.match?(code) && code != Jev::Classifier::ABSTENTION
    end

    def self.category_active?(brand, code)
      category_code?(code) && brand.categories.exists?(code: code, active: true)
    end

    def self.categories(brand)
      brand.categories.where(active: true).order(:code).pluck(:code, :name).to_h do |code, name|
        [code, CATEGORY_DESCRIPTIONS.fetch(code, name)]
      end
    end
  end
end
