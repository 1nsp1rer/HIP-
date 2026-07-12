"""Load the legacy native feature backend from this package."""

from __future__ import annotations

import ctypes
import importlib
import os
import sys
from pathlib import Path

import pandas as pd

from .feature_schema import FEATURES_36

NATIVE_DIR = Path(__file__).resolve().parent / "native"


class NativeBackendUnavailable(RuntimeError):
    """Raised when no legacy native backend can be loaded."""


def _load_pybind():
    native_path = str(NATIVE_DIR)
    if native_path not in sys.path:
        sys.path.insert(0, native_path)
    try:
        return importlib.import_module("_hip_features_pybind")
    except ImportError as exc:
        raise NativeBackendUnavailable(f"pybind backend is unavailable: {exc}") from exc


def _load_ctypes():
    dll_path = NATIVE_DIR / "_hip_features_ctypes.dll"
    if not dll_path.is_file():
        raise NativeBackendUnavailable(f"ctypes backend is unavailable: {dll_path.name} is missing")
    try:
        dll = ctypes.CDLL(str(dll_path))
    except OSError as exc:
        raise NativeBackendUnavailable(f"ctypes backend could not load {dll_path.name}: {exc}") from exc
    dll.hip_feature_count.restype = ctypes.c_int
    if dll.hip_feature_count() != len(FEATURES_36):
        raise NativeBackendUnavailable("ctypes backend feature count does not match the fixed schema")
    dll.hip_compute_features.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_double), ctypes.c_char_p, ctypes.c_size_t]
    dll.hip_compute_features.restype = ctypes.c_int
    return dll


def selected_backend() -> str:
    """Load and identify the backend using the original pybind, ctypes order."""
    preference = os.environ.get("HIP_CPP_BACKEND", "auto").strip().lower()
    if preference in {"", "auto", "pybind"}:
        try:
            _load_pybind()
            return "native pybind"
        except NativeBackendUnavailable:
            if preference == "pybind":
                raise
    if preference in {"", "auto", "ctypes"}:
        _load_ctypes()
        return "native ctypes DLL"
    raise NativeBackendUnavailable(f"Unknown HIP_CPP_BACKEND={preference!r}")


def build_feature_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    required = {"left", "right", "sequence"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing feature input columns: {missing}")
    backend = selected_backend()
    if backend == "native pybind":
        module = _load_pybind()
        rows = module.compute_feature_matrix([str(value) for value in df["left"]],
            [str(value) for value in df["right"]], [str(value) for value in df["sequence"]])
    else:
        dll = _load_ctypes()
        rows = []
        for left, right, sequence in zip(df["left"], df["right"], df["sequence"]):
            values = (ctypes.c_double * len(FEATURES_36))()
            error = ctypes.create_string_buffer(2048)
            code = dll.hip_compute_features(str(left).encode("ascii"), str(right).encode("ascii"),
                str(sequence).encode("ascii"), values, error, ctypes.sizeof(error))
            if code:
                raise RuntimeError(error.value.decode("utf-8", errors="replace"))
            rows.append(list(values))
    result = df.copy()
    features = pd.DataFrame(rows, columns=FEATURES_36)
    for column in FEATURES_36:
        result[column] = features[column]
    return result, backend
