from __future__ import annotations

from types import SimpleNamespace

import pytest
import torch

from pymss.separator import _prefer_mlx_for_auto, _resolve_public_device, _select_device, _store_torch_model_on_cpu_for_mlx


class DummyLogger:
    def debug(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass


def test_device_mlx_enables_clear_cache_by_default(monkeypatch):
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
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


@pytest.mark.parametrize(("backend", "device", "keep_cpu"), [
    ("mlx_full", "mps", True),
    ("torch", "mps", False),
    ("mlx_full", "cuda", False),
    ("mlx_full", "cpu", False),
])
def test_model_placement_follows_effective_backend(backend, device, keep_cpu):
    model = SimpleNamespace(mps_model_backend=backend)
    assert _store_torch_model_on_cpu_for_mlx(model, device) is keep_cpu


def test_model_without_mlx_support_is_not_left_on_cpu_for_mps():
    assert not _store_torch_model_on_cpu_for_mlx(torch.nn.Linear(2, 2), "mps")
