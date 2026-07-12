from pathlib import Path

from hip_features_score_gui.pipeline import calculate_batch


def test_batch_creates_independent_outputs(tmp_path: Path):
    source = Path(__file__).parent / "data" / "combined_example_small.fasta"
    copy = tmp_path / "second.fasta"
    copy.write_bytes(source.read_bytes())
    outputs = calculate_batch([source, copy], tmp_path / "output")
    assert [path.name for path in outputs] == ["combined_example_small_hip_full.csv", "second_hip_full.csv"]
    assert all(path.is_file() for path in outputs)
    assert all("score_rank" in path.read_text(encoding="utf-8-sig") for path in outputs)
