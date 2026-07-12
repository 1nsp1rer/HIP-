# Примеры

Папка `input` содержит подготовленные combined FASTA. Каждый файл представляет отдельное пространство кандидатов: выберите его через GUI, выберите выходную папку и нажмите **Calculate features + score**. Для каждого FASTA создаётся свой CSV; `score_0_1` и `score_rank` рассчитываются только внутри этого файла.

CSV не записывается в `examples/input`, если эта папка не выбрана явно. Для одного примера установите пакет и выполните `python -m hip_features_score_gui`, затем выберите любой файл из `input`.

---

# Examples

The `input` directory contains prepared combined FASTA files. Each file is a separate candidate space: select it in the GUI, choose an output directory, and click **Calculate features + score**. One CSV is created per FASTA, with `score_0_1` and `score_rank` calculated only within that file.

No output is written into `examples/input` unless you explicitly select that directory. To run an example, install the package, run `python -m hip_features_score_gui`, and choose any file from `input`.
