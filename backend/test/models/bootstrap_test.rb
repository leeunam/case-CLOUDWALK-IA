require "test_helper"

class BootstrapTest < ActiveSupport::TestCase
  setup do
    Rails.application.load_seed
  end

  test "executar o seed novamente preserva os registros existentes" do
    models = [
      Operations::Brand, Operations::Team, Operations::BrandTeam,
      Operations::SupportQueue, Operations::QueueTeam, Operations::Channel,
      Operations::Category, Operations::User, Operations::TeamMembership,
      Operations::SupervisorBrand, Operations::Attendant, Operations::CapacityProfile
    ]
    identities_before = models.to_h { |model| [model.name, model.order(:id).pluck(:id)] }

    Rails.application.load_seed

    assert_equal identities_before,
                 models.to_h { |model| [model.name, model.order(:id).pluck(:id)] }
    assert_equal 2, Operations::Brand.count
    assert_equal 3, Operations::Team.count
    assert_equal 4, Operations::SupportQueue.count
    assert_equal 6, Operations::Channel.count
    assert_equal 3, Operations::User.where(role: "analyst").count
    assert_equal 1, Operations::User.where(role: "supervisor").count
  end

  test "o banco rejeita uma equipe de outra marca mesmo sem validação do modelo" do
    aurora = Operations::Brand.find_by!(code: "aurora")
    horizonte = Operations::Brand.find_by!(code: "horizonte")
    queue = Operations::SupportQueue.find_by!(brand: aurora, code: "general")
    foreign_team = Operations::BrandTeam.find_by!(brand: horizonte)

    assert_raises ActiveRecord::InvalidForeignKey do
      ApplicationRecord.transaction(requires_new: true) do
        Operations::QueueTeam.insert_all!([
          { brand_id: aurora.id, support_queue_id: queue.id, brand_team_id: foreign_team.id }
        ])
      end
    end
  end

  test "o banco rejeita uma segunda fila padrão para a mesma marca" do
    aurora = Operations::Brand.find_by!(code: "aurora")

    assert_raises ActiveRecord::RecordNotUnique do
      ApplicationRecord.transaction(requires_new: true) do
        Operations::SupportQueue.insert_all!([
          { brand_id: aurora.id, code: "another_default", name: "Outra fila", active: true, is_default: true }
        ])
      end
    end
  end
end
