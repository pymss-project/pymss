from types import SimpleNamespace

import pytest
import torch

from pymss import devices
from pymss.separator import _resolve_public_device, _select_device


class Logger:
    def debug(self, *args):
        pass

    def warning(self, *args):
        pass


@pytest.fixture
def dml(monkeypatch):
    module = SimpleNamespace(
        is_available=lambda: True,
        device_count=lambda: 3,
        device_name=lambda index: ["Intel GPU", "AMD GPU", "NVIDIA GPU\x00"][index],
        device=lambda index: torch.device(f"privateuseone:{index}"),
    )
    monkeypatch.setattr(devices.util, "find_spec", lambda name: object())
    monkeypatch.setattr(devices, "import_module", lambda name: module)
    return module


def test_directml_discovery_includes_all_vendors(dml):
    assert devices.directml_devices() == [
        {"index": 0, "name": "Intel GPU"},
        {"index": 1, "name": "AMD GPU"},
        {"index": 2, "name": "NVIDIA GPU"},
    ]
    assert devices.directml_available()


def test_explicit_dml_selects_one_adapter(dml):
    assert _resolve_public_device("dml", {}, Logger()) == ("dml", {})
    assert _select_device("dml", [2], Logger()) == "privateuseone:2"


@pytest.mark.parametrize("ids", [[], [0, 1], [-1], [3], [True], [1.5]])
def test_invalid_adapter_selection_fails_instead_of_selecting_cpu(dml, ids):
    with pytest.raises(ValueError, match="DirectML"):
        devices.directml_device(ids)


def test_missing_directml_is_optional_for_cpu_but_required_when_requested(monkeypatch):
    monkeypatch.setattr(devices.util, "find_spec", lambda name: None)
    assert devices.directml_devices() == []
    assert not devices.directml_available()
    with pytest.raises(RuntimeError, match="requires torch-directml"):
        _select_device("dml", [0], Logger())


def test_no_usable_adapter_is_reported(dml):
    dml.device_count = lambda: 0
    dml.is_available = lambda: False
    assert not devices.directml_available()
    with pytest.raises(RuntimeError, match="DX12 adapter"):
        _select_device("dml", [0], Logger())


def test_auto_uses_dml_after_cuda_and_mps(dml, monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    assert _select_device("auto", [1], Logger()) == "privateuseone:1"
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 3)
    assert _select_device("auto", [1], Logger()) == "cuda:1"


def test_initialization_errors_are_not_hidden_as_cpu_fallback(monkeypatch):
    monkeypatch.setattr(devices.util, "find_spec", lambda name: object())

    def broken_import(name):
        raise OSError("DirectML DLL ABI mismatch")

    monkeypatch.setattr(devices, "import_module", broken_import)
    with pytest.raises(RuntimeError, match="ABI mismatch") as failure:
        devices.directml_available()
    assert isinstance(failure.value.__cause__, OSError)


@pytest.mark.parametrize("node_device,runtime_device,expected", [
    ("auto", "dml", "dml"),
    (None, "dml", "dml"),
    ("cpu", "dml", "cpu"),
    ("dml", "cpu", "dml"),
    ("auto", "cpu", "cpu"),
    ("auto", None, "auto"),
])
def test_graph_inherits_explicit_backend_without_overriding_node_device(node_device, runtime_device, expected):
    from pymss.graph.nodes import _common_separator_kwargs

    context = SimpleNamespace(device=runtime_device, logger=Logger(), debug=False, progress_callback=None)
    kwargs = _common_separator_kwargs(
        context, device=node_device, device_ids_raw="1", params={}, use_tta=False, debug=False, stems=["vocals"],
    )
    assert kwargs["device"] == expected
    assert kwargs["device_ids"] == [1]


@pytest.mark.parametrize("device", ["cpu", "cuda", "mps", "privateuseone:0"])
@pytest.mark.parametrize("outer_inference", [False, True])
def test_inference_context_preserves_caller_state_and_directml_tensor_versions(device, outer_inference):
    with torch.inference_mode(outer_inference):
        outer_grad = torch.is_grad_enabled()
        with devices.inference_context(device):
            expected_inference = not device.startswith("privateuseone")
            assert torch.is_inference_mode_enabled() is expected_inference
            assert not torch.is_grad_enabled()
            tensor = torch.ones(1)
            assert tensor.is_inference() is expected_inference
            if not expected_inference:
                assert tensor._version == 0
        assert torch.is_inference_mode_enabled() is outer_inference
        assert torch.is_grad_enabled() is outer_grad


@pytest.mark.parametrize("device", ["cpu", "privateuseone:0"])
@pytest.mark.parametrize("outer_inference", [False, True])
def test_separate_covers_device_transfers_and_restores_context_after_errors(device, outer_inference, monkeypatch):
    from pymss import MSSeparator

    separator = MSSeparator.__new__(MSSeparator)
    separator.device = device
    failure = RuntimeError("Separation failed")
    audio = object()
    def fail_separation(mix, *, pbar, stems, channel_layout):
        assert mix is audio and pbar is False and stems == ["vocals"] and channel_layout == "stereo"
        expected_inference = outer_inference if device == "cpu" else False
        assert torch.is_inference_mode_enabled() is expected_inference
        assert torch.is_grad_enabled() is (not outer_inference if device == "cpu" else False)
        assert torch.ones(1).is_inference() is expected_inference
        raise failure
    monkeypatch.setattr(separator, "_separate", fail_separation)
    with torch.inference_mode(outer_inference):
        with pytest.raises(RuntimeError) as caught:
            separator.separate(audio, pbar=False, stems=["vocals"], channel_layout="stereo")
        assert caught.value is failure
        assert torch.is_inference_mode_enabled() is outer_inference
        assert torch.is_grad_enabled() is (not outer_inference)
