from pathlib import Path

import pytest

from hip_features_score_gui import fasta_io


FIXTURE = Path(__file__).parent / "data" / "combined_example_small.fasta"


def test_multiple_records_and_separator_preserve_legacy_columns():
    records = fasta_io.read_fasta_records(FIXTURE)
    frame = fasta_io.build_input_dataframe(records)
    assert len(records) == 12
    assert list(frame.columns) == [
        "record_id", "header", "sequence_display", "sequence_plain", "left", "right",
        "left_len", "right_len", "sequence",
    ]
    assert frame.loc[0, "header"] == "INS_C_1-7_INS_A_1-7"
    assert frame.loc[0, "left"] == "EAEDLQV"
    assert frame.loc[0, "right"] == "GIVEQCC"


def test_multiline_fasta_is_joined(tmp_path: Path):
    fasta = tmp_path / "multiline.fasta"
    fasta.write_text(">record\nEAED\nLQV-GIV\nEQCC\n", encoding="utf-8")
    frame = fasta_io.build_input_dataframe(fasta_io.read_fasta_records(fasta))
    assert frame.loc[0, "sequence_display"] == "EAEDLQV-GIVEQCC"


@pytest.mark.parametrize(
    ("contents", "reason"),
    [(">bad\nEAEDLQV-GIVEXCC\n", "unknown amino-acid"), (">empty\n", "empty sequence")],
)
def test_invalid_records_report_file_record_header_and_reason(tmp_path: Path, contents: str, reason: str):
    fasta = tmp_path / "invalid.fasta"
    fasta.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError, match=reason) as exc:
        fasta_io.read_fasta_records(fasta)
    message = str(exc.value)
    assert str(fasta) in message
    assert "record 1" in message
    assert "header" in message


def test_missing_separator_uses_legacy_halves(tmp_path: Path):
    fasta = tmp_path / "plain.fasta"
    fasta.write_text(">plain\nEAEDLQVGIVEQCC\n", encoding="utf-8")
    frame = fasta_io.build_input_dataframe(fasta_io.read_fasta_records(fasta))
    assert frame.loc[0, "left"] == "EAEDLQV"
    assert frame.loc[0, "right"] == "GIVEQCC"
