"""The legacy fixed order of HIP feature columns."""

FEATURES_36 = [
    "junction_hydrophobicity", "junction_flexibility", "charge_balance", "length",
    "global_hydrophobicity", "total_charge", "anchor_residues", "asymmetry",
    "repeat_penalty", "junction_type_score", "delta_hydro", "delta_charge",
    "delta_flex", "mhc_anchor_score", "mhc_charge_penalty", "mhc_binding_proxy",
    "proline_count_junction", "glycine_count_junction", "has_proline_junction",
    "has_glycine_junction", "int_hydro_charge", "int_hydro_mhc", "int_anchor_hydro",
    "aa_0_class_hydrophobic", "aa_0_class_polar", "aa_0_class_charged",
    "aa_0_class_special", "junction_disorder", "junction_helix", "junction_turn",
    "compactness_proxy", "disorder_sq", "turn_sq", "hydro_disorder",
    "delta_flex_sq", "delta_hydro_flex",
]
