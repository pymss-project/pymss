import sys

import pytest

from pymss.modules._core_shims import alias_module


def test_alias_module_allows_pymss_core_modules():
    local_name = "pymss.modules._core_shims_test_spectrogram"

    try:
        module = alias_module(local_name, "pymss_core.modules.spectrogram")

        assert sys.modules[local_name] is module
        assert module.__name__ == "pymss_core.modules.spectrogram"
    finally:
        sys.modules.pop(local_name, None)


def test_alias_module_rejects_non_core_targets():
    local_name = "pymss.modules._core_shims_test_os"

    with pytest.raises(ValueError, match="invalid core module alias"):
        alias_module(local_name, "os")

    assert local_name not in sys.modules


def test_alias_module_rejects_non_pymss_local_names():
    with pytest.raises(ValueError, match="invalid local module alias"):
        alias_module("other.modules.spectrogram", "pymss_core.modules.spectrogram")
