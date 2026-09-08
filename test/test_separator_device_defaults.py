from __future__ import annotations

import pytest
import torch

from pymss.separator import _prefer_mlx_for_auto, _resolve_public_device, _select_device


class DummyLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass


def test_device_mlx_enables_clear_cache_by_default():
    device, params = _resolve_public_device("mlx", {}, DummyLogger())

    assert device == "mps"
    assert params["mps_model_backend"] == "mlx_full"
    assert params["mps_model_compute_dtype"] == "float16"
    assert params["mps_mlx_clear_cache"] is True


def test_auto_mps_mlx_full_enables_clear_cache_by_default():
    params = _prefer_mlx_for_auto("auto", "mps", {}, DummyLogger())

    assert params["mps_model_backend"] == "mlx_full"
    assert params["mps_model_compute_dtype"] == "float16"
    assert params["mps_mlx_clear_cache"] is True


def test_explicit_clear_cache_false_is_preserved():
    params = _prefer_mlx_for_auto("auto", "mps", {"mps_mlx_clear_cache": False}, DummyLogger())

    assert params["mps_model_backend"] == "mlx_full"
    assert params["mps_model_compute_dtype"] == "float16"
    assert params["mps_mlx_clear_cache"] is False


def test_device_rocm_maps_to_cuda(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.version, "hip", "6.4.47833", raising=False)

    device, params = _resolve_public_device("rocm", {}, DummyLogger())

    assert device == "cuda"
    assert params == {}


def test_device_rocm_requires_rocm_build(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    with pytest.raises(RuntimeError, match="rocm"):
        _resolve_public_device("rocm", {}, DummyLogger())


def test_select_device_auto_prefers_hip_as_cuda(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.version, "hip", "6.4.47833", raising=False)

    assert _select_device("auto", [0], DummyLogger()) == "cuda:0"


def test_select_device_cuda_prefers_hip_as_cuda(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.version, "hip", "6.4.47833", raising=False)

    assert _select_device("cuda", [0], DummyLogger()) == "cuda"
