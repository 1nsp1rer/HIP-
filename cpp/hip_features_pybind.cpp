#include "hip_features.hpp"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <ios>
#include <limits>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace py = pybind11;

namespace {

py::dict result_to_dict(const hip::FeatureResult& result) {
    py::dict out;
    for (std::size_t i = 0; i < hip::FEATURE_COUNT; ++i) {
        out[hip::FEATURE_NAMES[i]] = result.values[i];
    }
    return out;
}

py::array_t<double> compute_feature_matrix(
    const std::vector<std::string>& lefts,
    const std::vector<std::string>& rights,
    const std::vector<std::string>& sequences
) {
    if (lefts.size() != rights.size() || lefts.size() != sequences.size()) {
        throw hip::FeatureError("lefts, rights and sequences must have the same length");
    }

    py::array_t<double> rows({lefts.size(), hip::FEATURE_COUNT});
    auto out = rows.mutable_unchecked<2>();
    {
        py::gil_scoped_release release;

        const std::size_t row_count = lefts.size();
        const unsigned int hw_threads = std::max(1u, std::thread::hardware_concurrency());
        const std::size_t thread_count = std::min<std::size_t>(row_count, hw_threads);
        const std::size_t block_size = (row_count + thread_count - 1) / thread_count;

        std::vector<std::thread> threads;
        std::vector<std::exception_ptr> errors(thread_count);
        threads.reserve(thread_count);

        for (std::size_t t = 0; t < thread_count; ++t) {
            const std::size_t start = t * block_size;
            const std::size_t end = std::min(row_count, start + block_size);
            if (start >= end) {
                break;
            }
            threads.emplace_back([&, start, end, t]() {
                try {
                    for (std::size_t i = start; i < end; ++i) {
                        const auto result = hip::compute_features(lefts[i], rights[i], sequences[i]);
                        for (std::size_t j = 0; j < hip::FEATURE_COUNT; ++j) {
                            out(i, j) = result.values[j];
                        }
                    }
                } catch (...) {
                    errors[t] = std::current_exception();
                }
            });
        }

        for (auto& thread : threads) {
            thread.join();
        }

        for (const auto& error : errors) {
            if (error) {
                std::rethrow_exception(error);
            }
        }
    }
    return rows;
}

void write_csv_text(std::ostream& out, const std::string& value) {
    bool must_quote = value.find_first_of(",\"\r\n") != std::string::npos;
    if (!must_quote) {
        out << value;
        return;
    }

    out << '"';
    for (char ch : value) {
        if (ch == '"') {
            out << "\"\"";
        } else {
            out << ch;
        }
    }
    out << '"';
}

void write_csv_number(std::ostream& out, double value, int digits) {
    if (std::isnan(value)) {
        out << "nan";
        return;
    }
    if (std::isinf(value)) {
        out << (value > 0.0 ? "inf" : "-inf");
        return;
    }
    out << std::fixed << std::setprecision(digits) << value;
}

void write_feature_csv(
    const std::vector<std::string>& record_ids,
    const std::vector<std::string>& headers,
    const std::vector<std::string>& sequence_displays,
    const std::vector<std::string>& sequence_plains,
    const std::vector<std::string>& lefts,
    const std::vector<std::string>& rights,
    const std::vector<std::string>& sequences,
    const std::string& output_path,
    int float_digits
) {
    const std::size_t row_count = record_ids.size();
    if (
        headers.size() != row_count ||
        sequence_displays.size() != row_count ||
        sequence_plains.size() != row_count ||
        lefts.size() != row_count ||
        rights.size() != row_count ||
        sequences.size() != row_count
    ) {
        throw hip::FeatureError("all input columns must have the same length");
    }
    if (float_digits < 0 || float_digits > 15) {
        throw hip::FeatureError("float_digits must be between 0 and 15");
    }

    py::gil_scoped_release release;
    std::ofstream out(std::filesystem::u8path(output_path), std::ios::binary);
    if (!out) {
        throw hip::FeatureError("cannot open output CSV: " + output_path);
    }

    out << "record_id,header,sequence_display,sequence_plain,left,right,left_len,right_len,sequence";
    for (const char* name : hip::FEATURE_NAMES) {
        out << ',' << name;
    }
    out << '\n';

    for (std::size_t i = 0; i < row_count; ++i) {
        const auto result = hip::compute_features(lefts[i], rights[i], sequences[i]);

        write_csv_text(out, record_ids[i]);
        out << ',';
        write_csv_text(out, headers[i]);
        out << ',';
        write_csv_text(out, sequence_displays[i]);
        out << ',';
        write_csv_text(out, sequence_plains[i]);
        out << ',';
        write_csv_text(out, lefts[i]);
        out << ',';
        write_csv_text(out, rights[i]);
        out << ',' << lefts[i].size();
        out << ',' << rights[i].size();
        out << ',';
        write_csv_text(out, sequences[i]);

        for (std::size_t j = 0; j < hip::FEATURE_COUNT; ++j) {
            out << ',';
            write_csv_number(out, result.values[j], float_digits);
        }
        out << '\n';
    }
}

}  // namespace

PYBIND11_MODULE(_hip_features_pybind, m) {
    py::register_exception<hip::FeatureError>(m, "FeatureError");

    m.doc() = "C++ HIP240 feature calculator built with pybind11";
    m.attr("FEATURE_NAMES") = py::cast(hip::FEATURE_NAMES);

    m.def(
        "compute_features",
        [](const std::string& left, const std::string& right, const std::string& sequence) {
            return result_to_dict(hip::compute_features(left, right, sequence));
        },
        py::arg("left"),
        py::arg("right"),
        py::arg("sequence") = ""
    );

    m.def(
        "compute_feature_matrix",
        &compute_feature_matrix,
        py::arg("lefts"),
        py::arg("rights"),
        py::arg("sequences")
    );

    m.def(
        "write_feature_csv",
        &write_feature_csv,
        py::arg("record_ids"),
        py::arg("headers"),
        py::arg("sequence_displays"),
        py::arg("sequence_plains"),
        py::arg("lefts"),
        py::arg("rights"),
        py::arg("sequences"),
        py::arg("output_path"),
        py::arg("float_digits") = 4
    );
}
