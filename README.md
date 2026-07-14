# HIP Features and Ridge Score

The application accepts prepared FASTA files with HIP candidates, calculates the original 36 features, applies a fixed Ridge model, and writes a ranked CSV. A small GUI and a Python API are provided.

## Features

- one or multiple FASTA files;
- 36 HIP features and fixed Ridge scoring;
- per-file normalization and ranking;
- one compatible CSV for every input file;
- native C++ backend.

## Quick start

Windows x64 and CPython 3.12 are required.

```powershell
python -m pip install -r requirements.txt
python -m pip install .
python -m hip_features_score_gui
```

`run_gui.bat` and the `hip-features-score-gui` console command are also available after installation.

## Input format

Each prepared FASTA record is one HIP candidate. A hyphen separates the left and right peptide parts:

```text
>INS_C_1-7_INS_A_1-7
EAEDLQV-GIVEQCC
```

## Output format

Each input file produces its own CSV containing legacy metadata, 36 features, `score_raw`, `score_0_1`, and `score_rank`. Normalization and ranks are calculated independently for every FASTA.

## Examples

Prepared FASTA files are in [examples/input](examples/input). See [examples/README.md](examples/README.md) for usage.

## Validation

```powershell
python -m pytest tests -q
```

## Limitations

The bundled pybind backend supports Windows x64 and CPython 3.12. The included ctypes DLL is used only when pybind cannot load. Large FASTA files can require substantial time, memory, and output disk space.
