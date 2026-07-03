from __future__ import annotations

from pymss.separator import _prefer_mlx_for_auto, _resolve_public_device


class DummyLogger:
    def debug(self, *_args, **_kwargs):
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
    assert params["mps_mlx_clear_cache"] is False
