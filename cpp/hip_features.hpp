#pragma once

#include <array>
#include <cstddef>
#include <stdexcept>
#include <string>

namespace hip {

constexpr std::size_t FEATURE_COUNT = 36;

extern const std::array<const char*, FEATURE_COUNT> FEATURE_NAMES;

struct FeatureResult {
    std::array<double, FEATURE_COUNT> values{};
};

class FeatureError : public std::runtime_error {
public:
    explicit FeatureError(const std::string& message) : std::runtime_error(message) {}
};

FeatureResult compute_features(
    const std::string& left,
    const std::string& right,
    const std::string& sequence
);

}  // namespace hip
