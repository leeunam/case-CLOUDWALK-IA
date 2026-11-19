require "test_helper"

class HumanCapacityTest < ActiveSupport::TestCase
  test "cases must fit together in one complete alternative" do
    first = [["urgent", "pix", 1]]
    second = [["urgent", "terminal", 1], ["basic", "terminal", 1]]
    third = [["basic", "pix", 3], ["intermediate", "payouts", 1]]
    profile = Operations::CapacityProfile.new(alternatives: [first, second, third].map do |alternative|
      alternative.map { |priority, category, limit| { "priority" => priority, "category" => category, "limit" => limit } }
    end)

    assert profile.fits?({ %w[urgent pix] => 1 })
    refute profile.fits?({ %w[urgent pix] => 1, %w[basic pix] => 1 })
    assert profile.fits?({ %w[urgent terminal] => 1, %w[basic terminal] => 1 })
    assert profile.fits?({ %w[basic pix] => 3, %w[intermediate payouts] => 1 })
    refute profile.fits?({ %w[basic pix] => 4, %w[intermediate payouts] => 1 })
    refute profile.fits?({ %w[urgent pix] => 1, %w[urgent terminal] => 1 })
  end
end
