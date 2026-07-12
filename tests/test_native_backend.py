from pathlib import Path
import sys

import pandas as pd
import pytest

from hip_features_score_gui.feature_schema import FEATURES_36
from hip_features_score_gui import native_backend


@pytest.mark.skipif(sys.platform != "win32", reason="bundled native backends require Windows x64")
def test_bundled_native_backend_loads_from_package_and_returns_36_values():
    assert native_backend.NATIVE_DIR.is_dir()
    assert native_backend.NATIVE_DIR.parent == Path(native_backend.__file__).resolve().parent
    frame, backend = native_backend.build_feature_dataframe(pd.DataFrame([
        {"left": "EAEDLQV", "right": "GIVEQCC", "sequence": "EAEDLQVGIVEQCC"},
    ]))
    assert backend == native_backend.selected_backend()
    assert backend in {"native pybind", "native ctypes DLL"}
    assert list(frame.columns[-36:]) == FEATURES_36
