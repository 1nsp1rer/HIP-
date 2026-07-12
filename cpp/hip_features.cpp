#include "hip_features.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <sstream>
#include <string>
#include <unordered_set>

namespace hip {

const std::array<const char*, FEATURE_COUNT> FEATURE_NAMES = {
    "junction_hydrophobicity",
    "junction_flexibility",
    "charge_balance",
    "length",
    "global_hydrophobicity",
    "total_charge",
    "anchor_residues",
    "asymmetry",
    "repeat_penalty",
    "junction_type_score",
    "delta_hydro",
    "delta_charge",
    "delta_flex",
    "mhc_anchor_score",
    "mhc_charge_penalty",
    "mhc_binding_proxy",
    "proline_count_junction",
    "glycine_count_junction",
    "has_proline_junction",
    "has_glycine_junction",
    "int_hydro_charge",
    "int_hydro_mhc",
    "int_anchor_hydro",
    "aa_0_class_hydrophobic",
    "aa_0_class_polar",
    "aa_0_class_charged",
    "aa_0_class_special",
    "junction_disorder",
    "junction_helix",
    "junction_turn",
    "compactness_proxy",
    "disorder_sq",
    "turn_sq",
    "hydro_disorder",
    "delta_flex_sq",
    "delta_hydro_flex",
};

namespace {

constexpr const char* AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";

constexpr std::array<double, 20> HYDRO = {
    1.8, 2.5, -3.5, -3.5, 2.8, -0.4, -3.2, 4.5, -3.9, 3.8,
    1.9, -3.5, -1.6, -3.5, -4.5, -0.8, -0.7, 4.2, -0.9, -1.3,
};

constexpr std::array<double, 20> FLEXIBILITY = {
    0.35, 0.35, 0.50, 0.50, 0.35, 0.60, 0.35, 0.35, 0.50, 0.35,
    0.35, 0.50, 0.55, 0.50, 0.50, 0.55, 0.50, 0.35, 0.35, 0.35,
};

constexpr std::array<double, 20> DISORDER_PROXY = {
    0.20, NAN, NAN, 0.60, 0.20, 0.70, NAN, 0.20, NAN, 0.20,
    0.20, 0.60, 0.70, 0.60, NAN, 0.60, 0.60, 0.20, NAN, NAN,
};

constexpr std::array<double, 20> HELIX_PROXY = {
    1.45, NAN, NAN, 1.51, 1.20, 0.50, NAN, 1.08, NAN, 1.30,
    1.20, 0.67, 0.57, 1.11, NAN, 0.80, 0.83, 1.06, NAN, NAN,
};

constexpr std::array<double, 20> TURN_PROXY = {
    0.66, NAN, NAN, 0.74, 0.60, 1.50, NAN, 0.47, NAN, 0.50,
    0.60, 1.56, 1.52, 0.98, NAN, 1.20, 0.96, 0.50, NAN, NAN,
};

constexpr double DISORDER_PROXY_DEFAULT = 0.4307692307692308;
constexpr double HELIX_PROXY_DEFAULT = 1.0215384615384615;
constexpr double TURN_PROXY_DEFAULT = 0.9069230769230769;

bool contains(const char* chars, char aa) {
    for (const char* p = chars; *p != '\0'; ++p) {
        if (*p == aa) {
            return true;
        }
    }
    return false;
}

int aa_index(char aa) {
    for (int i = 0; AA_ORDER[i] != '\0'; ++i) {
        if (AA_ORDER[i] == aa) {
            return i;
        }
    }
    return -1;
}

std::string normalize_sequence(const std::string& raw) {
    std::string out;
    std::size_t first = raw.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        out = "";
    } else {
        std::size_t last = raw.find_last_not_of(" \t\r\n");
        out = raw.substr(first, last - first + 1);
    }

    std::unordered_set<char> bad;
    for (char& ch : out) {
        if (ch >= 'a' && ch <= 'z') {
            ch = static_cast<char>(ch - 'a' + 'A');
        }
        if (aa_index(ch) < 0) {
            bad.insert(ch);
        }
    }

    if (!bad.empty()) {
        std::string symbols;
        for (char ch : bad) {
            if (!symbols.empty()) {
                symbols += ", ";
            }
            symbols += ch;
        }
        throw FeatureError("Unknown amino-acid symbols in sequence '" + out + "': " + symbols);
    }
    return out;
}

std::string junction_window(const std::string& left, const std::string& right) {
    if (left.size() < 3 || right.size() < 3) {
        throw FeatureError("left and right fragments must each contain at least 3 residues");
    }
    return left.substr(left.size() - 3) + right.substr(0, 3);
}

std::string middle_9mer(const std::string& sequence) {
    if (sequence.size() < 9) {
        throw FeatureError("sequence must contain at least 9 residues");
    }
    std::size_t start = (sequence.size() - 9) / 2;
    return sequence.substr(start, 9);
}

double scale_value(char aa, const std::array<double, 20>& scale, const char* scale_name) {
    int idx = aa_index(aa);
    if (idx < 0 || std::isnan(scale[static_cast<std::size_t>(idx)])) {
        std::ostringstream oss;
        oss << scale_name << " has no value for residue '" << aa << "'";
        throw FeatureError(oss.str());
    }
    return scale[static_cast<std::size_t>(idx)];
}

double mean_scale(const std::string& seq, const std::array<double, 20>& scale, const char* scale_name) {
    if (seq.empty()) {
        throw FeatureError("cannot calculate mean scale for an empty sequence");
    }
    double sum = 0.0;
    for (char aa : seq) {
        sum += scale_value(aa, scale, scale_name);
    }
    return sum / static_cast<double>(seq.size());
}

double mean_scale_with_default(
    const std::string& seq,
    const std::array<double, 20>& scale,
    double default_value
) {
    if (seq.empty()) {
        throw FeatureError("cannot calculate mean scale for an empty sequence");
    }
    double sum = 0.0;
    for (char aa : seq) {
        int idx = aa_index(aa);
        if (idx < 0 || std::isnan(scale[static_cast<std::size_t>(idx)])) {
            sum += default_value;
        } else {
            sum += scale[static_cast<std::size_t>(idx)];
        }
    }
    return sum / static_cast<double>(seq.size());
}

int count_chars(const std::string& seq, const char* chars) {
    int count = 0;
    for (char aa : seq) {
        count += contains(chars, aa) ? 1 : 0;
    }
    return count;
}

int charge_balance(const std::string& seq) {
    return count_chars(seq, "KRH") - count_chars(seq, "DE");
}

int total_charge(const std::string& seq) {
    return count_chars(seq, "KR") - count_chars(seq, "DE");
}

int repeat_penalty(const std::string& seq) {
    if (seq.size() < 3) {
        return 0;
    }
    int count = 0;
    for (std::size_t i = 0; i + 2 < seq.size(); ++i) {
        if (seq[i] == seq[i + 1] && seq[i] == seq[i + 2]) {
            ++count;
        }
    }
    return count;
}

double round_half_up_6(double value) {
    constexpr double factor = 1000000.0;
    double scaled = value * factor;
    if (scaled >= 0.0) {
        return std::floor(scaled + 0.5) / factor;
    }
    return std::ceil(scaled - 0.5) / factor;
}

}  // namespace

FeatureResult compute_features(
    const std::string& raw_left,
    const std::string& raw_right,
    const std::string& raw_sequence
) {
    const std::string left = normalize_sequence(raw_left);
    const std::string right = normalize_sequence(raw_right);
    const std::string sequence = normalize_sequence(raw_sequence.empty() ? left + right : raw_sequence);

    if (sequence != left + right) {
        throw FeatureError("sequence != left + right for sequence='" + sequence + "'");
    }

    const std::string junc = junction_window(left, right);
    const std::string core = middle_9mer(sequence);
    const std::string left3 = left.substr(left.size() - 3);
    const std::string right3 = right.substr(0, 3);

    const double junction_hydrophobicity = mean_scale(junc, HYDRO, "HYDRO");
    const double junction_flexibility = static_cast<double>(count_chars(junc, "GPS")) / 6.0;
    const double charge_bal = static_cast<double>(charge_balance(sequence));
    const double length = static_cast<double>(sequence.size());
    const double global_hydrophobicity = mean_scale(sequence, HYDRO, "HYDRO");
    const double total_chg = static_cast<double>(total_charge(sequence));
    const double anchor_residues = static_cast<double>(count_chars(core, "FWY"));
    const double asymmetry = static_cast<double>(
        left.size() > right.size() ? left.size() - right.size() : right.size() - left.size()
    );
    const double repeat = static_cast<double>(repeat_penalty(sequence));
    const double junction_type = static_cast<double>(
        contains("AILMFWV", left.back()) && contains("AILMFWV", right.front())
    );

    const double delta_hydro = mean_scale(right3, HYDRO, "HYDRO") - mean_scale(left3, HYDRO, "HYDRO");
    const double delta_charge = static_cast<double>(total_charge(right3) - total_charge(left3));
    const double delta_flex =
        mean_scale(right3, FLEXIBILITY, "FLEXIBILITY") - mean_scale(left3, FLEXIBILITY, "FLEXIBILITY");

    double mhc_anchor_score = 0.0;
    for (std::size_t i : {0u, 3u, 5u, 8u}) {
        mhc_anchor_score += std::max(scale_value(core[i], HYDRO, "HYDRO"), 0.0);
    }
    mhc_anchor_score /= 4.0;

    double mhc_charge_penalty = 0.0;
    for (char aa : core) {
        std::string one(1, aa);
        mhc_charge_penalty += std::abs(total_charge(one));
    }
    mhc_charge_penalty /= 9.0;
    const double mhc_binding_proxy = mhc_anchor_score - mhc_charge_penalty;

    const double proline_count = static_cast<double>(std::count(junc.begin(), junc.end(), 'P'));
    const double glycine_count = static_cast<double>(std::count(junc.begin(), junc.end(), 'G'));

    const double aa0_hydrophobic = static_cast<double>(contains("AILMFWV", left.back()));
    const double aa0_polar = static_cast<double>(contains("STNQY", left.back()));
    const double aa0_charged = static_cast<double>(contains("DEKRH", left.back()));
    const double aa0_special = static_cast<double>(contains("GP", left.back()));

    const double junction_disorder = mean_scale_with_default(junc, DISORDER_PROXY, DISORDER_PROXY_DEFAULT);
    const double junction_helix = mean_scale_with_default(junc, HELIX_PROXY, HELIX_PROXY_DEFAULT);
    const double junction_turn = mean_scale_with_default(junc, TURN_PROXY, TURN_PROXY_DEFAULT);
    const double compactness_proxy =
        static_cast<double>(count_chars(junc, "AILMFWV")) / 6.0 -
        static_cast<double>(count_chars(junc, "DEKRH")) / 6.0;

    const double int_hydro_charge = delta_hydro * delta_charge;
    const double int_hydro_mhc = junction_hydrophobicity * mhc_binding_proxy;
    const double int_anchor_hydro = anchor_residues * delta_hydro;

    FeatureResult result;
    result.values = {
        junction_hydrophobicity,
        junction_flexibility,
        charge_bal,
        length,
        global_hydrophobicity,
        total_chg,
        anchor_residues,
        asymmetry,
        repeat,
        junction_type,
        delta_hydro,
        delta_charge,
        delta_flex,
        mhc_anchor_score,
        mhc_charge_penalty,
        mhc_binding_proxy,
        proline_count,
        glycine_count,
        proline_count > 0.0 ? 1.0 : 0.0,
        glycine_count > 0.0 ? 1.0 : 0.0,
        int_hydro_charge,
        int_hydro_mhc,
        int_anchor_hydro,
        aa0_hydrophobic,
        aa0_polar,
        aa0_charged,
        aa0_special,
        junction_disorder,
        junction_helix,
        junction_turn,
        compactness_proxy,
        junction_disorder * junction_disorder,
        junction_turn * junction_turn,
        junction_hydrophobicity * junction_disorder,
        round_half_up_6(delta_flex * delta_flex),
        round_half_up_6(delta_hydro * delta_flex),
    };
    return result;
}

}  // namespace hip
