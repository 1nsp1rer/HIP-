#include "hip_features.hpp"

#include <algorithm>
#include <cstring>

#if defined(_WIN32)
#define HIP_EXPORT extern "C" __declspec(dllexport)
#else
#define HIP_EXPORT extern "C"
#endif

namespace {

void copy_error(const char* message, char* error_buffer, std::size_t error_buffer_size) {
    if (error_buffer == nullptr || error_buffer_size == 0) {
        return;
    }
    std::strncpy(error_buffer, message, error_buffer_size - 1);
    error_buffer[error_buffer_size - 1] = '\0';
}

}  // namespace

HIP_EXPORT int hip_feature_count() {
    return static_cast<int>(hip::FEATURE_COUNT);
}

HIP_EXPORT const char* hip_feature_name(int index) {
    if (index < 0 || index >= static_cast<int>(hip::FEATURE_COUNT)) {
        return nullptr;
    }
    return hip::FEATURE_NAMES[static_cast<std::size_t>(index)];
}

HIP_EXPORT int hip_compute_features(
    const char* left,
    const char* right,
    const char* sequence,
    double* out_values,
    char* error_buffer,
    std::size_t error_buffer_size
) {
    if (left == nullptr || right == nullptr || out_values == nullptr) {
        copy_error("left, right and out_values must not be null", error_buffer, error_buffer_size);
        return 1;
    }

    try {
        const auto result = hip::compute_features(left, right, sequence == nullptr ? "" : sequence);
        std::copy(result.values.begin(), result.values.end(), out_values);
        copy_error("", error_buffer, error_buffer_size);
        return 0;
    } catch (const std::exception& exc) {
        copy_error(exc.what(), error_buffer, error_buffer_size);
        return 2;
    } catch (...) {
        copy_error("unknown C++ exception", error_buffer, error_buffer_size);
        return 3;
    }
}
