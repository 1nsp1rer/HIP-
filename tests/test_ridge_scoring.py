import pandas as pd

from hip_features_score_gui.feature_schema import FEATURES_36
from hip_features_score_gui.ridge_scoring import DEFAULT_COEFFICIENTS, DEFAULT_INTERCEPT, calculate_scores


def test_fixed_model_uses_the_36_feature_schema_in_order():
    assert list(DEFAULT_COEFFICIENTS) == FEATURES_36
    assert DEFAULT_INTERCEPT == 0.0729166667


def test_raw_score_normalization_sorting_and_ranking():
    frame = pd.DataFrame({name: [0.0, 0.0] for name in FEATURES_36})
    frame.loc[1, "length"] = 20.0
    result = calculate_scores(frame)
    assert result["score_0_1"].tolist() == [1.0, 0.0]
    assert result["score_rank"].tolist() == [1, 2]
    assert result["score_raw"].iloc[0] > result["score_raw"].iloc[1]


def test_equal_scores_keep_legacy_half_normalization():
    result = calculate_scores(pd.DataFrame({name: [0.0, 0.0] for name in FEATURES_36}))
    assert result["score_0_1"].tolist() == [0.5, 0.5]
    assert result["score_rank"].tolist() == [1, 2]
