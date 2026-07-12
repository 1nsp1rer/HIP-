@echo off
setlocal
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
py -3.12 -m hip_features_score_gui
if errorlevel 1 python -m hip_features_score_gui
