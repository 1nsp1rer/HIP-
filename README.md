# HIP Features and Ridge Score

Приложение принимает подготовленные FASTA-файлы с HIP-кандидатами, рассчитывает исходные 36 признаков, применяет фиксированную Ridge-модель и сохраняет ранжированный CSV. Доступны простой графический интерфейс и Python API.

## Возможности

- обработка одного или нескольких FASTA;
- 36 HIP-признаков и fixed Ridge scoring;
- независимые для каждого FASTA нормализация и ранжирование;
- один совместимый CSV на входной файл;
- native C++ backend.

## Быстрый запуск

Требуются Windows x64 и CPython 3.12.

```powershell
python -m pip install -r requirements.txt
python -m pip install .
python -m hip_features_score_gui
```

Также можно установить зависимости разработки (`python -m pip install -r requirements-dev.txt`) и запустить `run_gui.bat` или команду `hip-features-score-gui`.

## Формат входа

Подготовленный FASTA содержит один HIP-кандидат в записи. Дефис разделяет левую и правую части пептида:

```text
>INS_C_1-7_INS_A_1-7
EAEDLQV-GIVEQCC
```

## Формат выхода

Для каждого входного файла создаётся отдельный CSV со служебными полями исходного формата, 36 признаками, `score_raw`, `score_0_1` и `score_rank`. Нормализация и ранг рассчитываются только внутри соответствующего FASTA.

## Примеры

Подготовленные FASTA находятся в [examples/input](examples/input); описание — в [examples/README.md](examples/README.md). Выберите файл и выходную папку в GUI либо используйте API:

```python
from hip_features_score_gui import calculate_batch, calculate_features_and_score

calculate_features_and_score("combined_example.fasta", "combined_example_hip_full.csv")
calculate_batch(["first.fasta", "second.fasta"], "output")
```

## Проверка

```powershell
python -m pytest tests -q
```

## Ограничения

Bundled pybind backend предназначен для Windows x64 и CPython 3.12. Если pybind не загружается, приложение использует включённую ctypes DLL; большие FASTA могут требовать заметного времени, памяти и места для CSV. Инструкции пересборки находятся в [cpp/BUILD_WINDOWS.md](cpp/BUILD_WINDOWS.md).

---

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
