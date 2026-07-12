param([string]$Python = "C:\Python\python.exe")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& $Python -m pip install pybind11
& $Python setup.py build_ext --inplace
Copy-Item (Get-ChildItem -Filter "_hip_features_pybind*.pyd" | Select-Object -First 1).FullName "..\src\hip_features_score_gui\native\" -Force
