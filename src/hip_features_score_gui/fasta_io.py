"""Legacy-compatible prepared FASTA parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

VALID_SEQUENCE_SYMBOLS = frozenset("ACDEFGHIKLMNPQRSTVWY-_")


@dataclass(frozen=True)
class FastaRecord:
    number: int
    header: str
    sequence_display: str
    source: Path


def read_fasta_records(path: str | Path) -> list[FastaRecord]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"FASTA file not found: {source}")
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = source.read_text(encoding="cp1251")
    records: list[FastaRecord] = []
    header: str | None = None
    chunks: list[str] = []
    def finish() -> None:
        if header is None:
            return
        sequence = "".join(chunks).replace(" ", "").replace("\t", "")
        if not sequence:
            raise ValueError(f"Invalid FASTA {source}: record {len(records) + 1}, header {header!r}: empty sequence")
        invalid = sorted(set(sequence.upper()) - VALID_SEQUENCE_SYMBOLS)
        if invalid:
            symbols = ", ".join(invalid)
            raise ValueError(
                f"Invalid FASTA {source}: record {len(records) + 1}, header {header!r}: "
                f"unknown amino-acid symbol(s): {symbols}"
            )
        records.append(FastaRecord(len(records) + 1, header, sequence, source))
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip().lstrip("\ufeff")
        if not line:
            continue
        if line.startswith(">"):
            finish()
            header, chunks = line[1:].strip(), []
        elif header is None:
            raise ValueError(f"Invalid FASTA {source} at line {line_number}: sequence appears before a header")
        else:
            chunks.append(line)
    finish()
    if not records:
        raise ValueError(f"No FASTA records found in: {source}")
    return records


def build_input_dataframe(records: list[FastaRecord]) -> pd.DataFrame:
    rows = []
    for record in records:
        display = "".join(record.sequence_display.split()).upper()
        plain = "".join(display.replace("-", "").replace("_", "").split())
        try:
            if "-" in display:
                parts = [part for part in display.split("-") if part]
                if len(parts) != 2:
                    raise ValueError("a '-' sequence must contain exactly two non-empty parts")
                left, right = parts
                plain = left + right
            else:
                middle = len(plain) // 2
                if middle == 0 or middle == len(plain):
                    raise ValueError("sequence is too short to split into left and right parts")
                left, right = plain[:middle], plain[middle:]
        except Exception as exc:
            raise ValueError(
                f"Invalid FASTA {record.source}: record {record.number}, header {record.header!r}: {exc}"
            ) from exc
        rows.append({"record_id": f"seq_{record.number}", "header": record.header,
                     "sequence_display": record.sequence_display, "sequence_plain": plain,
                     "left": left, "right": right, "left_len": len(left), "right_len": len(right),
                     "sequence": plain})
    return pd.DataFrame(rows)
