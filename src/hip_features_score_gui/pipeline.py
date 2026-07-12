"""Public FASTA-to-scored-CSV pipeline."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, Iterable

from .csv_output import write_scored_csv
from .fasta_io import build_input_dataframe, read_fasta_records
from .native_backend import build_feature_dataframe, selected_backend
from .ridge_scoring import calculate_scores

ProgressCallback = Callable[[str], None]


def _report(callback: ProgressCallback | None, message: str) -> None:
    if callback:
        callback(message)


def calculate_features_and_score(
    fasta_path: str | Path,
    output_csv: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Calculate legacy features and a fixed Ridge score for one FASTA file."""
    fasta = Path(fasta_path)
    output = Path(output_csv)
    _report(progress_callback, "Reading FASTA...")
    records = read_fasta_records(fasta)
    _report(progress_callback, f"Candidates read: {len(records)}")
    _report(progress_callback, "Loading native backend...")
    inputs = build_input_dataframe(records)
    backend = selected_backend()
    _report(progress_callback, f"Feature backend: {backend}")
    _report(progress_callback, "Calculating 36 features...")
    features, _ = build_feature_dataframe(inputs)
    _report(progress_callback, "Calculating Ridge scores...")
    scored = calculate_scores(features)
    _report(progress_callback, "Sorting candidates...")
    output.parent.mkdir(parents=True, exist_ok=True)
    estimated_bytes = max(1, len(scored)) * max(512, len(scored.columns) * 16)
    if shutil.disk_usage(output.parent).free < estimated_bytes:
        raise OSError(f"Insufficient free disk space for output: {output.parent}")
    temporary = output.with_name(output.name + ".tmp")
    try:
        _report(progress_callback, "Writing CSV...")
        write_scored_csv(scored, temporary)
        os.replace(temporary, output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    _report(progress_callback, f"Output saved: {output}")
    return output


def calculate_batch(
    fasta_paths: Iterable[str | Path],
    output_directory: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> list[Path]:
    """Process FASTA files independently, preserving per-file normalization."""
    inputs = [Path(path) for path in fasta_paths]
    if not inputs:
        raise ValueError("Select at least one FASTA file")
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for index, fasta in enumerate(inputs, start=1):
        _report(progress_callback, f"Processing file {index}/{len(inputs)}: {fasta.name}")
        target = destination / f"{fasta.stem}_hip_full.csv"
        result = calculate_features_and_score(fasta, target, progress_callback)
        outputs.append(result)
        _report(progress_callback, f"Completed file {index}/{len(inputs)}")
    return outputs
