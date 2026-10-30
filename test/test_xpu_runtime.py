from types import SimpleNamespace

import pytest
import torch

from pymss import separator as separator_module
from test.test_separator_device_defaults import DummyLogger


def _available_xpu(monkeypatch, count=3):
    monkeypatch.setattr(separator_module, "_xpu_runtime_available", lambda: True)
    monkeypatch.setattr(torch, "xpu", SimpleNamespace(device_count=lambda: count), raising=False)


@pytest.mark.parametrize("device", ["xpu", "auto"])
@pytest.mark.parametrize("ids", [[0], [1], [2, 0]])
def test_xpu_selection_uses_the_requested_first_device(monkeypatch, device, ids):
    _available_xpu(monkeypatch)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    assert separator_module._select_device(device, ids, DummyLogger()) == f"xpu:{ids[0]}"


@pytest.mark.parametrize("device", ["xpu", "auto"])
@pytest.mark.parametrize("ids", [None, [], [-1], [3], [0, 3], [True], [1.5], ["1"]])
def test_invalid_xpu_ids_fail_before_loading_a_model(monkeypatch, device, ids):
    _available_xpu(monkeypatch)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(ValueError, match="XPU"):
        separator_module._select_device(device, ids, DummyLogger())


def test_auto_prefers_xpu_over_npu(monkeypatch):
    _available_xpu(monkeypatch)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(separator_module, "_npu_runtime_available", lambda: False)
    assert separator_module._select_device("auto", [0], DummyLogger()) == "xpu:0"


def test_auto_prefers_cuda_without_initializing_xpu(monkeypatch):
    def forbidden_probe():
        raise AssertionError("CUDA selection must not initialize XPU")

    monkeypatch.setattr(separator_module, "_xpu_runtime_available", forbidden_probe)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    assert separator_module._select_device("auto", [0], DummyLogger()) == "cuda:0"


def test_explicit_xpu_fails_when_runtime_is_unavailable(monkeypatch):
    monkeypatch.setattr(separator_module, "_xpu_runtime_available", lambda: False)
    with pytest.raises(RuntimeError, match="XPU-enabled"):
        separator_module._resolve_public_device("xpu", {}, DummyLogger())


@pytest.mark.parametrize(
    "argv",
    [
        ["infer", "model", "-i", "input.wav", "--device", "xpu"],
        ["workflow", "run", "-c", "workflow.yaml", "-i", "input.wav", "--device", "xpu"],
        ["comfy", "run", "-c", "workflow.json", "--device", "xpu"],
    ],
)
def test_cli_accepts_xpu(argv):
    from pymss.cli import build_parser

    assert build_parser().parse_args(argv).device == "xpu"
