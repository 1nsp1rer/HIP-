# Rebuilding the native backend

Use 64-bit Python 3.12 and Visual Studio Build Tools with the C++ desktop workload.

From this directory, run:

```powershell
.\build_pybind.ps1
.\build_ctypes.ps1
```

The application loads pybind first and uses ctypes only if the pybind module cannot be loaded.
