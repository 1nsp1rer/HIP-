"""Legacy CSV serialization."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import pandas as pd


def _format(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return f"{value:.4f}"
    return value


def write_scored_csv(df: pd.DataFrame, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(df.columns)
        for row in df.itertuples(index=False, name=None):
            writer.writerow([_format(value) for value in row])
    return output
