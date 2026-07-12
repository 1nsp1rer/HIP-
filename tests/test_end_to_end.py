from pathlib import Path

from hip_features_score_gui.pipeline import calculate_features_and_score


def test_pipeline_matches_legacy_expected_csv(tmp_path: Path):
    data = Path(__file__).parent / "data"
    actual = calculate_features_and_score(data / "combined_example_small.fasta", tmp_path / "actual.csv")
    expected = data / "combined_example_small_expected.csv"
    assert actual.read_bytes() == expected.read_bytes()
