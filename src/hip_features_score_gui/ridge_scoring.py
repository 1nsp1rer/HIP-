"""Fixed legacy Ridge scoring, normalization, sorting, and ranking."""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_INTERCEPT = 0.0729166667
DEFAULT_COEFFICIENTS = {
    "junction_hydrophobicity": (0.7207555962, 0.1916666542, 0.9509714917),
    "junction_flexibility": (-0.1392151994, 0.3791666583, 0.2050756260),
    "charge_balance": (0.3441512161, -2.0750000000, 2.0946734599),
    "length": (0.1146289874, 15.9000000000, 0.3006269599),
    "global_hydrophobicity": (-0.0454484605, -0.2424201333, 0.4749478915),
    "total_charge": (-0.2037319565, -2.5750000000, 1.6826085546),
    "anchor_residues": (0.1426091752, 0.3000000000, 0.4592152666),
    "asymmetry": (-0.1146289874, 0.1000000000, 0.3006269599),
    "repeat_penalty": (0.0552581030, 0.4666666667, 0.7536059294),
    "junction_type_score": (-0.0062321726, 0.1333333333, 0.3406450522),
    "delta_hydro": (0.0385262729, 0.0166666792, 1.9019430433),
    "delta_charge": (-0.0242377661, -0.2500000000, 0.8001045957),
    "delta_flex": (0.1541310601, -0.0254166667, 0.0712171638),
    "mhc_anchor_score": (-0.0022995146, 1.1108333333, 0.7426961889),
    "mhc_charge_penalty": (0.1545362141, 0.1731479750, 0.0956886267),
    "mhc_binding_proxy": (-0.0219329989, 0.9376853583, 0.7519312872),
    "proline_count_junction": (0.0091233442, 0.5500000000, 0.6317936213),
    "glycine_count_junction": (0.1406148523, 1.1750000000, 0.9520952451),
    "has_proline_junction": (-0.0076251961, 0.4750000000, 0.5004182351),
    "has_glycine_junction": (0.0495851327, 0.7375000000, 0.4409124241),
    "int_hydro_charge": (0.0273790489, 0.8469444500, 1.5237771243),
    "int_hydro_mhc": (-0.0336582273, 0.1383094083, 1.1463699549),
    "int_anchor_hydro": (0.0128406305, 0.1850000125, 0.8896726694),
    "aa_0_class_hydrophobic": (0.0440779823, 0.3333333333, 0.4723896933),
    "aa_0_class_polar": (-0.0103564951, 0.2083333333, 0.4069651601),
    "aa_0_class_charged": (0.0048086079, 0.0833333333, 0.2769630078),
    "aa_0_class_special": (-0.0369774816, 0.3750000000, 0.4851346705),
    "junction_disorder": (0.4494854833, 0.4793055167, 0.0748777533),
    "junction_helix": (0.4632773663, 0.9881944583, 0.1577147739),
    "junction_turn": (0.3093287729, 0.9768333125, 0.1492662814),
    "compactness_proxy": (0.6160182531, 0.2486111125, 0.2356981300),
    "disorder_sq": (0.3136605658, 0.2353170958, 0.0720693566),
    "turn_sq": (-0.2363500450, 0.9763908625, 0.2997160436),
    "hydro_disorder": (-0.6613106597, 0.0391990917, 0.4433771259),
    "delta_flex_sq": (-0.0259468976, 0.0056966750, 0.0077156790),
    "delta_hydro_flex": (-0.1581811320, -0.0819074417, 0.1537176079),
}


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the unmodified fixed model and legacy per-file normalization."""
    result = df.copy()
    missing = [name for name in DEFAULT_COEFFICIENTS if name not in result]
    if missing:
        raise ValueError("Missing score features: " + ", ".join(missing))
    score_raw = np.full(len(result), DEFAULT_INTERCEPT, dtype=float)
    for feature, (coefficient, mean, std) in DEFAULT_COEFFICIENTS.items():
        if std == 0:
            raise ValueError(f"Invalid fixed standard deviation for {feature}")
        values = pd.to_numeric(result[feature], errors="coerce").fillna(mean).astype(float).to_numpy()
        score_raw += coefficient * ((values - mean) / std)
    minimum = float(np.min(score_raw)) if len(score_raw) else np.nan
    maximum = float(np.max(score_raw)) if len(score_raw) else np.nan
    if not len(score_raw):
        score_0_1 = np.array([], dtype=float)
    elif abs(maximum - minimum) < 1e-15:
        score_0_1 = np.full(len(score_raw), 0.5, dtype=float)
    else:
        score_0_1 = (score_raw - minimum) / (maximum - minimum)
    result["score_raw"] = score_raw
    result["score_0_1"] = score_0_1
    result = result.sort_values("score_0_1", ascending=False).reset_index(drop=True)
    result.insert(0, "score_rank", np.arange(1, len(result) + 1))
    return result
