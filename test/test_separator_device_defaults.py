from __future__ import annotations

from pymss.separator import _cuda_runtime_name, _prefer_mlx_for_auto, _resolve_public_device, _select_device


class DummyLogger:
    def __init__(self):
        self.messages = []

    def debug(self, *args, **_kwargs):
        self.messages.append(("debug", args))

    def warning(self, *args, **_kwargs):
        self.messages.append(("warning", args))


def test_device_mlx_enables_clear_cache_by_default(monkeypatch):
    monkeypatch.setattr("torch.backends.mps.is_available", lambda: True)
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
    assert params["mps_mlx_clear_cache"] is False


def test_cuda_runtime_name_defaults_to_cuda(monkeypatch):
    monkeypatch.setattr("torch.version.hip", None, raising=False)

    assert _cuda_runtime_name() == "CUDA"


def test_cuda_runtime_name_uses_rocm_when_hip_is_present(monkeypatch):
    monkeypatch.setattr("torch.version.hip", "7.2.1", raising=False)

    assert _cuda_runtime_name() == "ROCm/HIP"


def test_select_device_prefers_cuda_and_logs_rocm_runtime(monkeypatch):
    logger = DummyLogger()
    monkeypatch.setattr("torch.cuda.is_available", lambda: True)
    monkeypatch.setattr("torch.version.hip", "7.2.1", raising=False)

    selected = _select_device("auto", [3], logger)

    assert selected == "cuda:3"
    assert any("ROCm/HIP" in args[0] for level, args in logger.messages if level == "debug")
