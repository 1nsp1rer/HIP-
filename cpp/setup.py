from __future__ import annotations

import os
from pathlib import Path

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ROOT = Path(__file__).resolve().parent
setup(
    name="hip_features_pybind",
    version="1.0.0",
    ext_modules=[Pybind11Extension("_hip_features_pybind", [str(ROOT / "hip_features.cpp"), str(ROOT / "hip_features_pybind.cpp")],
                                  cxx_std=17, extra_compile_args=["/O2"] if os.name == "nt" else ["-O3"],
                                  extra_link_args=["/MANIFEST:NO"] if os.name == "nt" else [])],
    cmdclass={"build_ext": build_ext},
)
