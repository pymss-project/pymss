"""Optional DirectML adapter discovery and device creation."""

from contextlib import contextmanager
from importlib import import_module, util

import torch


@contextmanager
def inference_context(device):
    """DirectML needs versioned tensors for views; keep gradients disabled."""
    if torch.device(device).type == "privateuseone":
        with torch.inference_mode(False), torch.no_grad():
            yield
    else:
        with torch.inference_mode():
            yield


def _directml():
    if util.find_spec("torch_directml") is None:
        raise RuntimeError("DirectML requires torch-directml; install pymss[dml] in a separate Windows environment")
    try:
        return import_module("torch_directml")
    except (ImportError, OSError, RuntimeError) as exc:
        raise RuntimeError(f"DirectML initialization failed: {exc}") from exc


def directml_available() -> bool:
    """Whether the optional backend has at least one usable DX12 adapter."""
    if util.find_spec("torch_directml") is None:
        return False
    return bool(_directml().is_available())


def directml_devices() -> list[dict[str, object]]:
    """Enumerate adapters by capability without filtering GPU vendors."""
    if util.find_spec("torch_directml") is None:
        return []
    dml = _directml()
    return [{"index": index, "name": str(dml.device_name(index)).rstrip("\x00")}
            for index in range(dml.device_count())]


def directml_device(device_ids):
    """Create one selected DirectML device; multi-GPU DataParallel is unsupported."""
    if len(device_ids) != 1:
        raise ValueError("DirectML requires exactly one adapter ID")
    index = device_ids[0]
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("DirectML adapter ID must be a non-negative integer")
    dml = _directml()
    count = dml.device_count()
    if not count:
        raise RuntimeError("DirectML found no usable DX12 adapter; check the GPU driver")
    if index >= count:
        raise ValueError(f"DirectML adapter ID {index} is outside the available range [0, {count})")
    return dml.device(index)
