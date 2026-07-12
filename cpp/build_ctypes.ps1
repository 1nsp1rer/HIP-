param([string]$Output = "..\src\hip_features_score_gui\native\_hip_features_ctypes.dll")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
cl /nologo /O2 /std:c++17 /EHsc /LD hip_features.cpp hip_features_dll.cpp /Fe:$Output
