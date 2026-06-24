from collections import deque
from contextlib import contextmanager, nullcontext
import gc
import json
import os
import re
import subprocess
import time

import numpy as np
import torch
import torch.nn as nn
from tqdm.auto import tqdm
from numpy.typing import NDArray
from typing import Dict

from .config import load_config


PRIVATE_ANE_MEMORY_TAIL_SAMPLES = 64
PRIVATE_ANE_TRANSFORMER_TIMING_TAIL = 64
PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT = 0
PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT = 0
PRIVATE_ANE_MAX_SWAP_USED_MB = 0.0
PRIVATE_ANE_FREE_MEMORY_STRIKES = 3
PRIVATE_ANE_MIN_ALLOWED_FREE_MEMORY_PERCENT = 30
PRIVATE_ANE_MIN_ALLOWED_EMERGENCY_FREE_MEMORY_PERCENT = 30
PRIVATE_ANE_MAX_ALLOWED_SWAP_USED_MB = 1536.0


class _ProgressContext:
    def __init__(self, pbar=False, total=1, callback=None, done=0, message="Processing audio chunks"):
        self.enabled = bool(pbar or callback)
        self.bar = None
        self.callback = callback
        self.done = done
        self.total = total
        self.message = message
        if not self.enabled:
            return
        self.bar = tqdm(total=total, desc=message, leave=False) if pbar else None
        self.total = int(self.total or 1)
        self.done = int(self.done or 0)
        self.emit()

    def emit(self, done=None):
        if not self.enabled:
            return
        if done is not None:
            self.done = int(done)
        if self.callback is None:
            return
        self.callback(min(self.done, self.total), self.total, self.message)

    def update(self, amount):
        if not self.enabled:
            return
        amount = int(amount)
        if self.bar:
            self.bar.update(amount)
        self.done += amount
        self.emit()

    def close(self):
        if not self.enabled:
            return
        if self.bar:
            self.bar.close()

def get_model_from_config(model_type, config_path, model_kwargs_override=None):
    model_kwargs_override = model_kwargs_override or {}
    config = load_config(config_path)

    if model_type == 'mdx23c':
        from .modules.mdx23c_tfc_tdf_v3 import TFC_TDF_net
        return TFC_TDF_net(config), config
    elif model_type == 'htdemucs':
        from .modules.demucs4ht import get_model
        return get_model(config), config
    elif model_type == 'mel_band_roformer':
        from .modules.bs_roformer import MelBandRoformer
        model_kwargs = dict(config.model)
        model_kwargs.update(model_kwargs_override)
        return MelBandRoformer(**model_kwargs), config
    elif model_type == 'bs_roformer':
        from .modules.bs_roformer import BSRoformer
        return BSRoformer(**dict(config.model)), config
    elif model_type == 'bs_roformer_hyperace':
        from .modules.bs_roformer import BSRoformerHyperACE
        return BSRoformerHyperACE(**dict(config.model)), config
    elif model_type == 'bandit':
        from .modules.bandit.core.model import MultiMaskMultiSourceBandSplitRNNSimple
        return MultiMaskMultiSourceBandSplitRNNSimple(**config.model), config
    elif model_type == 'bandit_v2':
        from .modules.bandit_v2.bandit import Bandit
        return Bandit(**config.kwargs), config
    elif model_type == 'scnet':
        from .modules.scnet import SCNet
        return SCNet(**config.model), config
    elif model_type == 'apollo':
        from .modules.look2hear.apollo import Apollo
        return Apollo(**config.model), config
    elif model_type == 'vr':
        raise ValueError("VR models are loaded directly by MSSeparator and do not use YAML config loading")
    raise ValueError(f"Model type {model_type} not supported")

def _getWindowingArray(window_size, fade_size):
    if fade_size <= 0:
        return torch.ones(window_size)

    fadein = torch.linspace(0, 1, fade_size)
    fadeout = torch.linspace(1, 0, fade_size)
    window = torch.ones(window_size)
    window[-fade_size:] *= fadeout
    window[:fade_size] *= fadein
    return window


def _build_chunk_plan(total_length, chunk_size, step, fade_size):
    starts = list(range(0, total_length, step))
    normal_window = _getWindowingArray(chunk_size, fade_size)

    def window_for(start):
        length = min(chunk_size, total_length - start)
        if start != 0 and start + length < total_length:
            return normal_window
        window = normal_window.clone()
        if start == 0:
            window[:fade_size] = 1
        if start + length >= total_length:
            window[max(0, length - fade_size):length] = 1
        return window

    return starts, [window_for(start) for start in starts]


def _get_inference_step(config, chunk_size):
    overlap_size = int(config.inference.get('overlap_size', chunk_size // 2))
    if overlap_size < 0 or overlap_size >= chunk_size:
        raise ValueError("inference.overlap_size must be >= 0 and < audio.chunk_size")
    return chunk_size - overlap_size


def _complete_chunk_count(total_length, chunk_size, step):
    return 0 if total_length < chunk_size else (total_length - chunk_size) // step + 1


def _fold_windows(counter, windows, step, start_offset=0):
    n_chunks = windows.shape[0]
    if n_chunks == 0:
        return

    chunk_size = windows.shape[-1]
    output_length = (n_chunks - 1) * step + chunk_size
    folded_counter = nn.functional.fold(
        windows.transpose(0, 1).unsqueeze(0),
        output_size=(1, output_length),
        kernel_size=(1, chunk_size),
        stride=(1, step),
    )
    counter[..., start_offset:start_offset + output_length] += folded_counter.view(1, 1, output_length)


def _fold_chunk_batch(result, chunks, windows, step, start_offset=0):
    n_chunks = chunks.shape[0]
    if n_chunks == 0:
        return

    chunk_size = chunks.shape[-1]
    output_length = (n_chunks - 1) * step + chunk_size
    n_sources, n_channels = chunks.shape[1:3]

    folded = nn.functional.fold(
        (chunks * windows[:, None, None, :]).permute(1, 2, 3, 0).reshape(
            1, n_sources * n_channels * chunk_size, n_chunks
        ),
        output_size=(1, output_length),
        kernel_size=(1, chunk_size),
        stride=(1, step),
    )
    result[..., start_offset:start_offset + output_length] += folded.view(n_sources, n_channels, output_length)


def _ensure_source_dim(x, chunk_batch):
    return x.unsqueeze(1) if x.ndim == chunk_batch.ndim else x


def _fit_tensor_length(x, length):
    if x.shape[-1] > length:
        return x[..., :length]
    if x.shape[-1] < length:
        return nn.functional.pad(x, (0, length - x.shape[-1]))
    return x


def _autocast(device, enabled):
    device_type = torch.device(device).type
    if enabled and device_type in ('cuda', 'mps'):
        return torch.amp.autocast(device_type, dtype=torch.float16)
    return nullcontext()


def _source_names(config):
    return config.training.instruments if config.training.target_instrument is None else [config.training.target_instrument]


def _normalize_source_indices(config, source_indices):
    if source_indices is None:
        return None
    source_count = len(_source_names(config))
    indices = tuple(int(index) for index in source_indices)
    if not indices:
        raise ValueError("source_indices must not be empty")
    if len(set(indices)) != len(indices):
        raise ValueError("source_indices must not contain duplicates")
    if min(indices) < 0 or max(indices) >= source_count:
        raise ValueError(f"source_indices must be in range [0, {source_count})")
    return indices


def _source_count(config, source_indices=None):
    return len(_source_names(config)) if source_indices is None else len(source_indices)


def _sources_to_dict(config, estimated_sources, source_indices=None):
    names = _source_names(config)
    if source_indices is not None:
        names = [names[index] for index in source_indices]
    return {k: v for k, v in zip(names, estimated_sources)}


def _prepare_mix_for_chunks(mix, border):
    length_init = mix.shape[-1]
    mix = mix.unsqueeze(0) if mix.ndim == 1 else mix
    if length_init > 2 * border and border > 0:
        mix = nn.functional.pad(mix, (border, border), mode='reflect')
    return mix, length_init


def _current_rss_mb():
    try:
        rss_pages = int(subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())], text=True).strip())
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None
    return rss_pages / 1024.0


def _system_free_memory_percent():
    try:
        output = subprocess.check_output(["memory_pressure"], text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", output)
    return None if match is None else int(match.group(1))


def _system_swap_used_mb():
    try:
        output = subprocess.check_output(["sysctl", "vm.swapusage"], text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"used\s*=\s*([0-9.]+)([KMG])", output)
    if match is None:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit == "K":
        return value / 1024.0
    if unit == "G":
        return value * 1024.0
    return value


def _ane_service_rss_mb():
    try:
        output = subprocess.check_output(["ps", "-axo", "rss=,command="], text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    total_kb = 0
    for line in output.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        rss_text, command = parts
        if (
                "ANECompilerService" not in command
                and "/usr/libexec/aned" not in command
                and "/usr/libexec/aneuserd" not in command
        ):
            continue
        try:
            total_kb += int(rss_text)
        except ValueError:
            continue
    return total_kb / 1024.0


def _release_private_ane_batch_memory():
    started = time.perf_counter()
    gc_started = time.perf_counter()
    gc.collect()
    gc_sec = time.perf_counter() - gc_started
    mps_empty_cache_sec = 0.0
    if hasattr(torch, "mps") and torch.backends.mps.is_available():
        try:
            mps_started = time.perf_counter()
            torch.mps.empty_cache()
            mps_empty_cache_sec = time.perf_counter() - mps_started
        except RuntimeError:
            pass
    return {
        "wall_sec": float(time.perf_counter() - started),
        "gc_sec": float(gc_sec),
        "mps_empty_cache_sec": float(mps_empty_cache_sec),
    }


def _private_ane_trace_event(event, **fields):
    path = os.environ.get("PYMSS_PRIVATE_ANE_TRACE_PATH")
    if not path:
        return
    row = {"time_sec": time.time(), "event": event}
    for key, value in fields.items():
        if value is not None:
            row[key] = value
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
            handle.flush()
    except OSError:
        pass


@contextmanager
def _private_ane_runner_cleanup(model):
    env_keys = ("TMPDIR", "ANE_BRIDGE_TMPDIR", "ANE_BRIDGE_LOAD_CACHE", "ANE_BRIDGE_KEEP_TMPDIR")
    old_env = {key: os.environ.get(key) for key in env_keys}
    try:
        yield
    finally:
        runner = getattr(model, "_private_ane_runner", None)
        persistent_transformer = _private_ane_bool_config(
            getattr(model, "private_ane_persistent_transformer_handles", False)
        )
        if runner is not None and persistent_transformer and hasattr(runner, "clear_non_transformer_cache"):
            try:
                runner.clear_non_transformer_cache(preserve_aux_handles=False)
            except Exception:
                pass
        elif runner is not None and hasattr(runner, "clear_cache"):
            try:
                runner.clear_cache()
            except Exception:
                pass
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        _release_private_ane_batch_memory()


def _private_ane_bool_config(value):
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def _private_ane_config_or_model(config, model, key, default=None):
    missing = object()
    value = config.inference.get(key, missing)
    if value is missing:
        return getattr(model, key, default)
    return value


def _private_ane_bool_config_or_model(config, model, key, default=False):
    return _private_ane_bool_config(_private_ane_config_or_model(config, model, key, default))


def _private_ane_optional_int(value, default=None):
    if value in (None, "", 0, "0"):
        return default
    if value == "default":
        return default
    return int(value)


def _resolve_private_ane_chunk_batch_size(config, chunk_count, max_chunks):
    value = config.inference.get("private_ane_chunk_batch_size", None)
    defaulted_to_auto = value in (None, "")
    if value in (None, ""):
        value = "auto"
    if value not in ("auto", 0, "0"):
        chunk_batch_size = int(value)
        if chunk_batch_size < 1:
            raise ValueError("inference.private_ane_chunk_batch_size must be >= 1, 0, or 'auto'")
        return chunk_batch_size, "explicit", None

    max_auto = _private_ane_optional_int(
        config.inference.get("private_ane_auto_chunk_batch_max", 4),
        4,
    )
    if max_auto is None or max_auto < 1:
        raise ValueError("inference.private_ane_auto_chunk_batch_max must be >= 1")
    limit = chunk_count if max_chunks is None else min(chunk_count, max_chunks)
    target = max(1, min(limit, max_auto))
    min_free = _private_ane_optional_int(
        config.inference.get("private_ane_auto_chunk_batch_min_free_memory_percent", 55),
        55,
    )
    free_percent = _system_free_memory_percent() if target > 1 and min_free is not None else None
    if target > 1 and min_free is not None and (free_percent is None or free_percent < min_free):
        return 1, "auto_default_memory_limited" if defaulted_to_auto else "auto_memory_limited", {
            "requested": int(target),
            "selected": 1,
            "max": int(max_auto),
            "free_memory_percent": free_percent,
            "min_free_memory_percent": int(min_free),
        }
    return target, "auto_default" if defaulted_to_auto else "auto", {
        "requested": int(target),
        "selected": int(target),
        "max": int(max_auto),
        "free_memory_percent": free_percent,
        "min_free_memory_percent": int(min_free) if min_free is not None else None,
    }


def _resolve_private_ane_transformer_cache_segments(config, model, chunk_count, chunk_batch_size):
    explicit = config.inference.get("private_ane_transformer_cache_segments", 0)
    allow_handle_cache = _private_ane_bool_config(
        config.inference.get(
            "private_ane_allow_transformer_handle_cache",
            getattr(model, "private_ane_allow_transformer_handle_cache", False),
        )
    )
    if explicit not in (None, "", 0, "0"):
        segments = int(explicit)
        if segments < 0:
            raise ValueError("inference.private_ane_transformer_cache_segments must be >= 0")
        if not allow_handle_cache:
            raise ValueError(
                "inference.private_ane_transformer_cache_segments > 0 is disabled by default "
                "because even segments=1 has triggered system wired-memory pressure on this machine. "
                "Set private_ane_allow_transformer_handle_cache=True only for native-supervised experiments."
            )
        return segments, "explicit", {
            "enabled": True,
            "selected": int(segments),
            "allow_transformer_handle_cache": True,
            "reason": "explicit_experimental",
        }

    chunk_batch_size = max(1, int(chunk_batch_size))
    batch_count = (int(chunk_count) + chunk_batch_size - 1) // chunk_batch_size
    auto_enabled = _private_ane_bool_config(
        config.inference.get(
            "private_ane_auto_transformer_cache_segments",
            getattr(model, "private_ane_auto_transformer_cache_segments", True),
        )
    )
    if not auto_enabled:
        return 0, "auto_disabled", {
            "enabled": False,
            "selected": 0,
            "allow_transformer_handle_cache": bool(allow_handle_cache),
        }
    if not allow_handle_cache:
        return 0, "auto_disabled_wired_memory_risk", {
            "enabled": False,
            "selected": 0,
            "allow_transformer_handle_cache": False,
            "reason": "wired_memory_risk",
        }
    if batch_count > 1:
        return 0, "auto_disabled_multi_batch", {
            "enabled": False,
            "selected": 0,
            "batch_count": int(batch_count),
            "allow_transformer_handle_cache": bool(allow_handle_cache),
            "reason": "multi_batch_wired_memory_guard",
        }

    layer_count = len(getattr(model, "layers", ()))
    max_layers = config.inference.get(
        "private_ane_max_transformer_layers",
        getattr(model, "private_ane_max_transformer_layers", None),
    )
    if max_layers in (None, "", 0, "0"):
        active_layers = layer_count
    else:
        active_layers = min(layer_count, max(0, int(max_layers)))
    requested = max(0, active_layers * 2)
    max_auto_value = config.inference.get(
        "private_ane_auto_transformer_cache_max_segments",
        getattr(model, "private_ane_auto_transformer_cache_max_segments", 0),
    )
    max_auto = 0 if max_auto_value in (None, "", 0, "0") else int(max_auto_value)
    if max_auto is None or max_auto < 1:
        return 0, "auto_disabled_max_segments_zero", {
            "enabled": False,
            "batch_count": int(batch_count),
            "requested": int(requested),
            "selected": 0,
            "max": 0,
            "allow_transformer_handle_cache": bool(allow_handle_cache),
            "reason": "max_segments_zero",
        }
    selected = min(requested, int(max_auto))
    auto = {
        "enabled": True,
        "batch_count": int(batch_count),
        "requested": int(requested),
        "selected": int(selected),
        "max": int(max_auto),
        "allow_transformer_handle_cache": bool(allow_handle_cache),
    }
    if batch_count <= 1 or selected <= 0:
        auto["reason"] = "single_batch" if batch_count <= 1 else "no_active_layers"
        auto["selected"] = 0
        return 0, "auto_not_needed", auto

    min_free = _private_ane_optional_int(
        config.inference.get(
            "private_ane_auto_transformer_cache_min_free_memory_percent",
            getattr(model, "private_ane_auto_transformer_cache_min_free_memory_percent", 55),
        ),
        55,
    )
    free_percent = _system_free_memory_percent() if min_free is not None else None
    auto["free_memory_percent"] = free_percent
    auto["min_free_memory_percent"] = int(min_free) if min_free is not None else None
    if min_free is not None and (free_percent is None or free_percent < min_free):
        auto["reason"] = "memory_limited"
        auto["selected"] = 0
        return 0, "auto_memory_limited", auto
    auto["reason"] = "selected"
    return selected, "auto", auto


def _init_overlap_buffers(config, mix, device, use_fast_path, source_indices=None):
    req_shape = (_source_count(config, source_indices),) + tuple(mix.shape)
    result_device = device if use_fast_path else 'cpu'
    counter_shape = (1, 1, mix.shape[1])
    result = torch.zeros(req_shape, dtype=torch.float32, device=result_device)
    counter = torch.zeros(counter_shape, dtype=torch.float32, device=result_device)
    return result, counter


def _model_mix(mix, device):
    return mix.to(device) if torch.device(device).type != 'cpu' else mix


@contextmanager
def _model_source_context(model, source_indices):
    target = model.module if isinstance(model, nn.DataParallel) else model
    sentinel = object()
    previous = getattr(target, "_pymss_source_indices", sentinel)
    if source_indices is not None:
        target._pymss_source_indices = source_indices
    try:
        yield
    finally:
        if previous is sentinel:
            if hasattr(target, "_pymss_source_indices"):
                delattr(target, "_pymss_source_indices")
        else:
            target._pymss_source_indices = previous


def _select_sources(chunks, source_indices, already_selected=False):
    if source_indices is None or already_selected:
        return chunks
    index = torch.as_tensor(source_indices, device=chunks.device)
    return chunks.index_select(1, index)


def _run_model_chunk(model, arr, chunk_size, source_indices=None):
    target = model.module if isinstance(model, nn.DataParallel) else model
    chunks = _fit_tensor_length(_ensure_source_dim(model(arr), arr).float(), chunk_size)
    already_selected = (
        source_indices is not None
        and hasattr(target, "_active_source_indices")
        and chunks.shape[1] == len(source_indices)
    )
    return _select_sources(chunks, source_indices, already_selected=already_selected)


def _extract_chunk(mix, start, chunk_size):
    length = min(chunk_size, mix.shape[1] - start)
    part = mix[:, start:start + chunk_size]
    if length == chunk_size:
        return part, length
    if length > chunk_size // 2 + 1:
        part = nn.functional.pad(part, (0, chunk_size - length), mode='reflect')
    else:
        part = nn.functional.pad(part, (0, chunk_size - length, 0, 0), mode='constant', value=0)
    return part, length


def _add_weighted_chunk(result, counter, chunk, window, start, length):
    device = result.device
    window = window.to(device=device, dtype=torch.float32)[:length]
    result[..., start:start + length] += chunk[..., :length].to(device=device, dtype=torch.float32) * window
    counter[..., start:start + length] += window


def _run_complete_chunks(
    model,
    mix,
    windows,
    result,
    counter,
    chunk_size,
    step,
    batch_size,
    progress,
    source_indices=None,
):
    n_chunks = _complete_chunk_count(mix.shape[1], chunk_size, step)
    if n_chunks == 0:
        return 0

    n_complete = n_chunks
    if len(windows) > n_chunks:
        n_complete -= n_complete % batch_size
    if n_complete == 0:
        return 0

    inputs = mix.unfold(-1, chunk_size, step).permute(1, 0, 2)[:n_complete]
    fold_windows = torch.stack(windows[:n_complete], dim=0).to(device=result.device, dtype=torch.float32)
    _fold_windows(counter, fold_windows, step)

    for batch_start in range(0, n_complete, batch_size):
        batch_end = min(batch_start + batch_size, n_complete)
        chunks = _run_model_chunk(model, inputs[batch_start:batch_end].contiguous(), chunk_size, source_indices)
        _fold_chunk_batch(
            result,
            chunks,
            fold_windows[batch_start:batch_end],
            step,
            start_offset=batch_start * step,
        )
        progress.update(step * (batch_end - batch_start))

    return n_complete


def _run_tail_chunks(
    model,
    mix,
    starts,
    windows,
    result,
    counter,
    chunk_size,
    step,
    batch_size,
    first_chunk,
    progress,
    source_indices=None,
):
    for batch_start in range(first_chunk, len(starts), batch_size):
        batch_indices = range(batch_start, min(batch_start + batch_size, len(starts)))
        batch = [(_extract_chunk(mix, starts[idx], chunk_size), idx) for idx in batch_indices]
        batch_data = [chunk for (chunk, _), _ in batch]
        chunks = _run_model_chunk(model, torch.stack(batch_data, dim=0), chunk_size, source_indices)
        for j, ((_, length), idx) in enumerate(batch):
            start = starts[idx]
            _add_weighted_chunk(result, counter, chunks[j], windows[idx], start, length)

        progress.update(step * len(batch_data))


def _finalize_overlap(result, counter, length_init, border):
    if length_init > 2 * border and border > 0:
        start, end = border, border + length_init
    else:
        start, end = 0, result.shape[-1]

    result = result[..., start:end]
    counter = counter[..., start:end]
    output_shape = result.shape[:-1] + (end - start,)

    if torch.device(result.device).type != "cuda":
        estimated_sources = (result / counter).cpu().numpy()
        np.nan_to_num(estimated_sources, copy=False, nan=0.0)
        return estimated_sources

    counter_min, counter_max = torch.aminmax(counter)
    divide_counter = bool((counter_min - 1).abs().item() > 1e-6 or (counter_max - 1).abs().item() > 1e-6)
    samples_per_chunk = max(1, (512 * 1024 * 1024) // (max(1, result.shape[0] * result.shape[1]) * 4))
    estimated_sources_t = torch.empty(output_shape, dtype=torch.float32, device="cpu")
    for offset in range(0, result.shape[-1], samples_per_chunk):
        chunk_end = min(offset + samples_per_chunk, result.shape[-1])
        source = result[..., offset:chunk_end]
        if divide_counter:
            source = source / counter[..., offset:chunk_end]
        estimated_sources_t[..., offset:chunk_end].copy_(source)
    estimated_sources = estimated_sources_t.numpy()
    if divide_counter:
        np.nan_to_num(estimated_sources, copy=False, nan=0.0)
    return estimated_sources


def _mlx_reflect_pad_1d(x, left=0, right=0):
    import mlx.core as mx

    parts = []
    if left > 0:
        parts.append(x[..., 1:left + 1][..., ::-1])
    parts.append(x)
    if right > 0:
        parts.append(x[..., -right - 1:-1][..., ::-1])
    return mx.concatenate(parts, axis=-1)


def _mlx_get_windowing_array(window_size, fade_size):
    import mlx.core as mx

    if fade_size <= 0:
        return mx.ones((window_size,), dtype=mx.float32)
    fadein = mx.linspace(0, 1, fade_size)
    fadeout = mx.linspace(1, 0, fade_size)
    window = mx.ones((window_size,), dtype=mx.float32)
    window = window.at[:fade_size].multiply(fadein)
    window = window.at[-fade_size:].multiply(fadeout)
    return window


def _mlx_build_chunk_plan(total_length, chunk_size, step, fade_size):
    starts = list(range(0, total_length, step))
    normal_window = _mlx_get_windowing_array(chunk_size, fade_size)
    windows = []
    for start in starts:
        length = min(chunk_size, total_length - start)
        if start != 0 and start + length < total_length:
            windows.append(normal_window)
            continue
        window = normal_window
        if start == 0 and fade_size > 0:
            window = window.at[:fade_size].add(1 - window[:fade_size])
        if start + length >= total_length and fade_size > 0:
            tail = slice(max(0, length - fade_size), length)
            window = window.at[tail].add(1 - window[tail])
        windows.append(window)
    return starts, windows


def _mlx_prepare_mix_for_chunks(mix, border):
    import mlx.core as mx

    length_init = mix.shape[-1]
    mix = mx.array(np.asarray(mix, dtype=np.float32))
    if mix.ndim == 1:
        mix = mix[None, :]
    if length_init > 2 * border and border > 0:
        mix = _mlx_reflect_pad_1d(mix, border, border)
    return mix, length_init


def _mlx_extract_chunk(mix, start, chunk_size):
    import mlx.core as mx

    length = min(chunk_size, mix.shape[1] - start)
    part = mix[:, start:start + chunk_size]
    if length == chunk_size:
        return part, length
    pad = chunk_size - length
    if length > chunk_size // 2 + 1:
        part = _mlx_reflect_pad_1d(part, right=pad)
    else:
        part = mx.pad(part, [(0, 0), (0, pad)])
    return part, length


def _mlx_fit_length(x, length):
    import mlx.core as mx

    if x.shape[-1] > length:
        return x[..., :length]
    if x.shape[-1] < length:
        return mx.pad(x, [(0, 0)] * (x.ndim - 1) + [(0, length - x.shape[-1])])
    return x


def _mlx_run_model_chunk(model, arr, chunk_size):
    y = model.mlx_forward_mx(arr)
    if y.ndim == arr.ndim:
        y = y[:, None]
    return _mlx_fit_length(y, chunk_size)


def _mlx_select_sources(chunks, source_indices):
    if source_indices is None:
        return chunks

    import mlx.core as mx

    return mx.take(chunks, mx.array(source_indices, dtype=mx.int32), axis=1)


def _mlx_add_weighted_chunk(result, counter, chunk, window, start, length):
    import mlx.core as mx

    window = window[:length].astype(result.dtype)
    weighted = chunk[..., :length].astype(result.dtype) * window
    positions = mx.arange(start, start + length)
    return result.at[:, :, positions].add(weighted), counter.at[:, :, positions].add(window)


def _mlx_finalize_overlap(result, counter, length_init, border):
    import mlx.core as mx

    estimated_sources = result / counter
    if length_init > 2 * border and border > 0:
        estimated_sources = estimated_sources[..., border:-border]
    estimated_sources = np.array(estimated_sources, copy=False)
    np.nan_to_num(estimated_sources, copy=False, nan=0.0)
    return estimated_sources


def _can_demix_mlx_full(model, device):
    return (
        torch.device(device).type == "mps"
        and getattr(model, "mps_model_backend", None) == "mlx_full"
        and hasattr(model, "mps_model_compute_dtype")
        and hasattr(model, "mlx_forward_mx")
    )


def _can_demix_coreml_ane_segmented(model, device):
    return (
        getattr(model, "mps_model_backend", None) == "coreml_ane_segmented"
        and hasattr(model, "coreml_ane_compute_unit")
    )


def _can_demix_private_ane(model, device):
    return getattr(model, "mps_model_backend", None) == "private_ane"


def demix_track_coreml_ane_segmented(config, model, mix, device, pbar=False, source_indices=None, progress_callback=None):
    from .modules.bs_roformer.common import istft_roformer, stft_roformer
    from .modules.bs_roformer.coreml_ane import coreml_ane_forward_mask_core

    C = int(config.audio.chunk_size)
    source_indices = _normalize_source_indices(config, source_indices)
    step = _get_inference_step(config, C)
    border = C - step
    fade_size = min(C // 10, border)

    mix = torch.as_tensor(mix, dtype=torch.float32)
    mix, length_init = _prepare_mix_for_chunks(mix, border)
    starts, windows = _build_chunk_plan(mix.shape[1], C, step, fade_size)
    progress = _ProgressContext(pbar, mix.shape[1], progress_callback)

    if not starts:
        progress.close()
        progress.emit(mix.shape[1])
        empty = np.zeros((_source_count(config, source_indices), mix.shape[0], 0), dtype=np.float32)
        return _sources_to_dict(config, empty, source_indices)

    chunk_parts = []
    chunk_lengths = []
    for start in starts:
        chunk, length = _extract_chunk(mix, start, C)
        chunk_parts.append(chunk)
        chunk_lengths.append(length)

    with torch.inference_mode():
        with _model_source_context(model, source_indices):
            batch = torch.stack(chunk_parts, dim=0).float()
            stft_repr, context = stft_roformer(model, batch)
            mask = coreml_ane_forward_mask_core(model, stft_repr)
            stft_complex = torch.view_as_complex(stft_repr.unsqueeze(1).contiguous())
            mask_complex = torch.view_as_complex(mask.contiguous()).type(stft_complex.dtype)
            chunks = istft_roformer(model, stft_complex * mask_complex, context, context.audio_length).float()
            if chunks.ndim == 3:
                chunks = chunks.unsqueeze(1)
            chunks = _select_sources(chunks.cpu(), source_indices)

    result = torch.zeros((_source_count(config, source_indices), mix.shape[0], mix.shape[1]), dtype=torch.float32)
    counter = torch.zeros((1, 1, mix.shape[1]), dtype=torch.float32)
    for chunk, window, start, length in zip(chunks, windows, starts, chunk_lengths, strict=True):
        _add_weighted_chunk(result, counter, chunk, window, start, length)
        progress.update(step)

    progress.close()
    progress.emit(mix.shape[1])
    return _sources_to_dict(config, _finalize_overlap(result, counter, length_init, border), source_indices)


def demix_track_private_ane(config, model, mix, device, pbar=False, source_indices=None, progress_callback=None):
    from .modules.bs_roformer.common import istft_roformer, stft_roformer
    from .modules.bs_roformer.private_ane import (
        _runner,
        private_ane_forward_mask_core_batch_layerwise,
        private_ane_istft_roformer,
        private_ane_stft_roformer,
    )

    C = int(config.audio.chunk_size)
    source_indices = _normalize_source_indices(config, source_indices)
    step = _get_inference_step(config, C)
    border = C - step
    fade_size = min(C // 10, border)

    mix = torch.as_tensor(mix, dtype=torch.float32)
    mix, length_init = _prepare_mix_for_chunks(mix, border)
    starts, windows = _build_chunk_plan(mix.shape[1], C, step, fade_size)
    progress = _ProgressContext(pbar, mix.shape[1], progress_callback)

    if not starts:
        progress.close()
        progress.emit(mix.shape[1])
        empty = np.zeros((_source_count(config, source_indices), mix.shape[0], 0), dtype=np.float32)
        return _sources_to_dict(config, empty, source_indices)

    max_chunks = config.inference.get("private_ane_max_chunks", 1)
    max_chunks = None if max_chunks in (None, "", 0, "0") else int(max_chunks)
    allow_long_audio = _private_ane_bool_config(config.inference.get("private_ane_allow_long_audio", False))
    if max_chunks is not None and len(starts) > max_chunks and not allow_long_audio:
        raise RuntimeError(
            "private_ane refused to run a long input by default: "
            f"{len(starts)} chunks > private_ane_max_chunks={max_chunks}. "
            "Pass private_ane_allow_long_audio=True only after a short smoke test is stable."
        )
    defer_istft_until_after_masks = _private_ane_bool_config(
        config.inference.get("private_ane_defer_istft_until_after_masks", False)
    )

    chunk_batch_size, chunk_batch_size_mode, chunk_batch_auto = _resolve_private_ane_chunk_batch_size(
        config,
        len(starts),
        max_chunks,
    )
    transformer_cache_segments, transformer_cache_segments_mode, transformer_cache_auto = (
        _resolve_private_ane_transformer_cache_segments(config, model, len(starts), chunk_batch_size)
    )
    transformer_timing_tail_limit = config.inference.get(
        "private_ane_transformer_timing_tail",
        PRIVATE_ANE_TRANSFORMER_TIMING_TAIL,
    )
    transformer_timing_tail_limit = (
        None if transformer_timing_tail_limit in (None, "", 0, "0")
        else int(transformer_timing_tail_limit)
    )
    if transformer_timing_tail_limit is not None and transformer_timing_tail_limit < 1:
        raise ValueError("private_ane_transformer_timing_tail must be >= 1, or 0 to keep all timings")
    max_rss_mb = config.inference.get("private_ane_max_rss_mb", 1792)
    max_rss_mb = None if max_rss_mb in (None, "", 0, "0") else float(max_rss_mb)
    min_free_memory_percent = config.inference.get(
        "private_ane_min_free_memory_percent",
        PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT,
    )
    min_free_memory_percent = (
        None if min_free_memory_percent in (None, "", 0, "0") else int(min_free_memory_percent)
    )
    if (
            min_free_memory_percent is not None
            and min_free_memory_percent < PRIVATE_ANE_MIN_ALLOWED_FREE_MEMORY_PERCENT
    ):
        raise ValueError(
            "inference.private_ane_min_free_memory_percent must be >= "
            f"{PRIVATE_ANE_MIN_ALLOWED_FREE_MEMORY_PERCENT}, or 0 to disable the soft guard"
        )
    emergency_free_memory_percent = config.inference.get(
        "private_ane_emergency_free_memory_percent",
        PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT,
    )
    emergency_free_memory_percent = (
        None if emergency_free_memory_percent in (None, "", 0, "0") else int(emergency_free_memory_percent)
    )
    if (
            emergency_free_memory_percent is not None
            and emergency_free_memory_percent < PRIVATE_ANE_MIN_ALLOWED_EMERGENCY_FREE_MEMORY_PERCENT
    ):
        raise ValueError(
            "inference.private_ane_emergency_free_memory_percent must be >= "
            f"{PRIVATE_ANE_MIN_ALLOWED_EMERGENCY_FREE_MEMORY_PERCENT}, or 0 to disable"
        )
    max_ane_service_rss_mb = config.inference.get("private_ane_max_ane_service_rss_mb", 512)
    max_ane_service_rss_mb = (
        None if max_ane_service_rss_mb in (None, "", 0, "0") else float(max_ane_service_rss_mb)
    )
    max_swap_used_mb = config.inference.get("private_ane_max_swap_used_mb", PRIVATE_ANE_MAX_SWAP_USED_MB)
    max_swap_used_mb = None if max_swap_used_mb in (None, "", 0, "0") else float(max_swap_used_mb)
    if (
            max_swap_used_mb is not None
            and (max_swap_used_mb < 0 or max_swap_used_mb > PRIVATE_ANE_MAX_ALLOWED_SWAP_USED_MB)
    ):
        raise ValueError(
            "inference.private_ane_max_swap_used_mb must be <= "
            f"{PRIVATE_ANE_MAX_ALLOWED_SWAP_USED_MB}, or 0 to disable"
        )
    free_memory_strikes_limit = int(
        config.inference.get("private_ane_free_memory_strikes", PRIVATE_ANE_FREE_MEMORY_STRIKES)
        or PRIVATE_ANE_FREE_MEMORY_STRIKES
    )
    if free_memory_strikes_limit < 1:
        raise ValueError("inference.private_ane_free_memory_strikes must be >= 1")
    low_free_memory_strikes = 0
    memory_samples = deque(maxlen=PRIVATE_ANE_MEMORY_TAIL_SAMPLES)
    memory_sample_count = 0
    max_observed_rss_mb = None
    min_observed_free_memory_percent = None
    max_observed_ane_service_rss_mb = None
    max_observed_swap_used_mb = None

    def _runner_cache_counts(runner):
        if runner is None or not hasattr(runner, "cache_handle_counts"):
            return None
        try:
            return dict(runner.cache_handle_counts())
        except Exception:
            return None

    def sample_memory(label, batch_index, extra=None):
        nonlocal low_free_memory_strikes
        nonlocal memory_sample_count
        nonlocal max_observed_rss_mb
        nonlocal min_observed_free_memory_percent
        nonlocal max_observed_ane_service_rss_mb
        nonlocal max_observed_swap_used_mb
        sample = {"label": label, "batch": int(batch_index)}
        if isinstance(extra, dict):
            for key, value in extra.items():
                if value is not None:
                    sample[key] = value
        rss_mb = _current_rss_mb()
        free_percent = _system_free_memory_percent()
        ane_service_rss_mb = _ane_service_rss_mb()
        swap_used_mb = _system_swap_used_mb()
        if rss_mb is not None:
            sample["rss_mb"] = float(rss_mb)
            max_observed_rss_mb = (
                float(rss_mb)
                if max_observed_rss_mb is None
                else max(max_observed_rss_mb, float(rss_mb))
            )
        if free_percent is not None:
            sample["free_memory_percent"] = int(free_percent)
            min_observed_free_memory_percent = (
                int(free_percent)
                if min_observed_free_memory_percent is None
                else min(min_observed_free_memory_percent, int(free_percent))
            )
        if ane_service_rss_mb is not None:
            sample["ane_service_rss_mb"] = float(ane_service_rss_mb)
            max_observed_ane_service_rss_mb = (
                float(ane_service_rss_mb)
                if max_observed_ane_service_rss_mb is None
                else max(max_observed_ane_service_rss_mb, float(ane_service_rss_mb))
            )
        if swap_used_mb is not None:
            sample["swap_used_mb"] = float(swap_used_mb)
            max_observed_swap_used_mb = (
                float(swap_used_mb)
                if max_observed_swap_used_mb is None
                else max(max_observed_swap_used_mb, float(swap_used_mb))
            )
        memory_sample_count += 1
        memory_samples.append(sample)
        if max_rss_mb is not None and rss_mb is not None and rss_mb > max_rss_mb:
            raise MemoryError(
                f"private_ane RSS exceeded limit: {rss_mb:.1f} MB > {max_rss_mb:.1f} MB"
            )
        if (
                emergency_free_memory_percent is not None
                and free_percent is not None
                and free_percent < emergency_free_memory_percent
        ):
            raise MemoryError(
                "private_ane stopped because system memory is below the emergency floor: "
                f"{free_percent}% < {emergency_free_memory_percent}% at {label}"
            )
        if (
                max_ane_service_rss_mb is not None
                and ane_service_rss_mb is not None
                and ane_service_rss_mb > max_ane_service_rss_mb
        ):
            raise MemoryError(
                "private_ane ANE service RSS exceeded limit: "
                f"{ane_service_rss_mb:.1f} MB > {max_ane_service_rss_mb:.1f} MB"
            )
        if max_swap_used_mb is not None and swap_used_mb is not None and swap_used_mb > max_swap_used_mb:
            raise MemoryError(
                "private_ane stopped because system swap usage is high: "
                f"{swap_used_mb:.1f} MB > {max_swap_used_mb:.1f} MB at {label}"
            )
        if (
            min_free_memory_percent is not None
            and free_percent is not None
            and free_percent < min_free_memory_percent
        ):
            low_free_memory_strikes += 1
            if low_free_memory_strikes >= free_memory_strikes_limit:
                raise MemoryError(
                    "private_ane stopped because system free memory is low: "
                    f"{free_percent}% < {min_free_memory_percent}% "
                    f"for {low_free_memory_strikes} consecutive samples"
                )
        else:
            low_free_memory_strikes = 0

    sample_memory("before_result_allocation", 0)
    result = torch.zeros((_source_count(config, source_indices), mix.shape[0], mix.shape[1]), dtype=torch.float32)
    counter = torch.zeros((1, 1, mix.shape[1]), dtype=torch.float32)

    original_transformer_cache_segments = getattr(model, "private_ane_transformer_cache_segments", 0)
    model.private_ane_transformer_cache_segments = transformer_cache_segments
    try:
        with _private_ane_runner_cleanup(model), torch.inference_mode(), _model_source_context(model, source_indices):
            private_ane_batch_summaries = []
            private_ane_stft_summaries = []
            private_ane_istft_summaries = []
            pending_istft_items = []
            cache_release_events = []
            stft_preload_timing = None
            stft_cache_releases = 0
            irfft_cache_releases = 0
            aux_cache_releases = 0
            batch_cache_releases = 0
            transformer_cache_releases = 0

            def runner_preserves_aux_handles(runner) -> bool:
                if runner is None or not hasattr(runner, "preserve_aux_handles_between_batches"):
                    return False
                return bool(runner.preserve_aux_handles_between_batches())

            def runner_preserves_stft_handles(runner) -> bool:
                if runner is None or not hasattr(runner, "preserve_stft_handles_between_batches"):
                    return False
                return bool(runner.preserve_stft_handles_between_batches())

            def should_release_non_transformer_handles(cache_handles, preserve_aux_handles, preserve_stft_handles):
                stale_aux = int(cache_handles.get("aux_handles", 0) or 0)
                stale_stft = int(cache_handles.get("stft_handles", 0) or 0)
                stale_irfft = int(cache_handles.get("irfft_handles", 0) or 0)
                return (
                    stale_irfft > 0
                    or (stale_stft > 0 and not preserve_stft_handles)
                    or (stale_aux > 0 and not preserve_aux_handles)
                )

            def release_runner_cache(label, batch_index, method_name, context=None, method_kwargs=None):
                runner = getattr(model, "_private_ane_runner", None)
                if runner is None or not hasattr(runner, method_name):
                    return None
                method_kwargs = dict(method_kwargs or {})
                before = _runner_cache_counts(runner)
                trace_context = dict(context or {})
                trace_context.pop("batch", None)
                _private_ane_trace_event(
                    "cache_release_start",
                    label=label,
                    batch=int(batch_index),
                    method=method_name,
                    cache_handles=before,
                    **trace_context,
                )
                release_method = getattr(runner, method_name)
                release_started = time.perf_counter()
                release_summary = release_method(**method_kwargs)
                release_wall_sec = time.perf_counter() - release_started
                if not isinstance(release_summary, dict):
                    after = _runner_cache_counts(runner)
                    released = {}
                    if before is not None and after is not None:
                        released = {
                            key: max(0, int(value) - int(after.get(key, 0)))
                            for key, value in before.items()
                        }
                    release_summary = {
                        "before": before,
                        "after": after,
                        "released": released,
                        "released_total_handles": int(released.get("total_handles", 0)),
                    }
                if method_kwargs:
                    release_summary["method_kwargs"] = method_kwargs
                release_summary["wall_sec"] = float(release_wall_sec)
                event = {
                    "label": label,
                    "batch": int(batch_index),
                    "method": method_name,
                    "summary": release_summary,
                }
                if isinstance(context, dict):
                    for key, value in context.items():
                        if value is not None:
                            event[key] = value
                cache_release_events.append(event)
                sample_extra = dict(context or {})
                sample_extra["cache_handles"] = release_summary.get("after")
                sample_extra["cache_release"] = release_summary.get("released")
                sample_extra["cache_release_method"] = method_name
                sample_memory(f"after_{label}", batch_index, sample_extra)
                _private_ane_trace_event(
                    "cache_release_done",
                    label=label,
                    batch=int(batch_index),
                    method=method_name,
                    cache_handles=release_summary.get("after"),
                    released=release_summary.get("released"),
                    wall_sec=float(release_wall_sec),
                    **trace_context,
                )
                return release_summary

            sample_memory("start", 0)
            _private_ane_trace_event(
                "demix_start",
                chunks=len(starts),
                chunk_batch_size=int(chunk_batch_size),
                transformer_cache_segments=int(transformer_cache_segments or 0),
                transformer_cache_segments_mode=transformer_cache_segments_mode,
            )
            if _private_ane_bool_config_or_model(config, model, "private_ane_preload_stft_handles", False):
                runner = _runner(model)
                _private_ane_trace_event("stft_preload_start", cache_handles=_runner_cache_counts(runner))
                preload_started = time.perf_counter()
                stft_preload_timing = runner.preload_stft_handles()
                stft_preload_timing["wall_sec"] = float(time.perf_counter() - preload_started)
                preload_context = {"cache_handles": _runner_cache_counts(runner)}
                sample_memory("after_stft_preload", 0, preload_context)
                _private_ane_trace_event(
                    "stft_preload_done",
                    cache_handles=preload_context["cache_handles"],
                    **stft_preload_timing,
                )
            for batch_start in range(0, len(starts), chunk_batch_size):
                batch_index = batch_start // chunk_batch_size
                batch_end = min(batch_start + chunk_batch_size, len(starts))
                batch_chunk_indices = list(range(batch_start, batch_end))
                batch_chunk_starts = [int(starts[idx]) for idx in batch_chunk_indices]
                batch_context = {
                    "batch": int(batch_index),
                    "batch_start": int(batch_start),
                    "batch_end": int(batch_end),
                    "batch_chunk_indices": [int(idx) for idx in batch_chunk_indices],
                    "batch_chunk_starts": batch_chunk_starts,
                    "batch_chunk_count": int(batch_end - batch_start),
                }
                _private_ane_trace_event("batch_start", **batch_context)
                runner = getattr(model, "_private_ane_runner", None)
                if runner is not None:
                    runner.memory_context = dict(batch_context)
                    cache_handles = _runner_cache_counts(runner)
                    if cache_handles is not None:
                        stale_non_transformer = int(cache_handles.get("non_transformer_handles", 0) or 0)
                        stale_transformer = int(cache_handles.get("transformer_handles", 0) or 0)
                        preserve_aux_handles = runner_preserves_aux_handles(runner)
                        preserve_stft_handles = runner_preserves_stft_handles(runner)
                        should_release_non_transformer = stale_non_transformer > 0 and should_release_non_transformer_handles(
                            cache_handles,
                            preserve_aux_handles,
                            preserve_stft_handles,
                        )
                        if should_release_non_transformer or (
                                stale_transformer > 0
                                and transformer_cache_segments_mode != "explicit"
                        ):
                            release_method = (
                                "clear_cache"
                                if stale_transformer > 0 and transformer_cache_segments_mode != "explicit"
                                else "clear_non_transformer_cache"
                            )
                            if hasattr(runner, release_method):
                                release_kwargs = {}
                                if release_method in ("clear_cache", "clear_non_transformer_cache"):
                                    release_kwargs["preserve_aux_handles"] = preserve_aux_handles
                                    release_kwargs["preserve_stft_handles"] = preserve_stft_handles
                                release_runner_cache(
                                    "pre_batch_stale_cache_release",
                                    batch_index,
                                    release_method,
                                    batch_context,
                                    release_kwargs,
                                )
                batch_sample_context = dict(batch_context)
                cache_handles = _runner_cache_counts(runner)
                if cache_handles is not None:
                    batch_sample_context["cache_handles"] = cache_handles
                sample_memory("before_batch", batch_index, batch_sample_context)
                stft_items = []
                for idx in range(batch_start, batch_end):
                    chunk, length = _extract_chunk(mix, starts[idx], C)
                    stft_started = time.perf_counter()
                    _private_ane_trace_event(
                        "stft_start",
                        batch=int(batch_index),
                        chunk_index=int(idx),
                        chunk_start=int(starts[idx]),
                        chunk_valid_length=int(length),
                    )
                    stft_repr, context = private_ane_stft_roformer(model, chunk)
                    _private_ane_trace_event(
                        "stft_done",
                        batch=int(batch_index),
                        chunk_index=int(idx),
                        wall_sec=float(time.perf_counter() - stft_started),
                    )
                    stft_summary = getattr(model, "_pymss_private_ane_last_stft", {}) or {}
                    stft_summary = dict(stft_summary)
                    stft_summary["wall_sec"] = float(time.perf_counter() - stft_started)
                    private_ane_stft_summaries.append(stft_summary)
                    stft_items.append((stft_repr, context, windows[idx], starts[idx], length))
                    del chunk

                runner = getattr(model, "_private_ane_runner", None)
                cache_handles = _runner_cache_counts(runner) or {}
                if (
                        runner is not None
                        and hasattr(runner, "clear_stft_cache")
                        and not runner_preserves_stft_handles(runner)
                        and int(cache_handles.get("stft_handles", 0) or 0) > 0
                ):
                    release_runner_cache("stft_cache_release", batch_index, "clear_stft_cache", batch_context)
                    stft_cache_releases += 1

                _private_ane_trace_event("mask_batch_start", **batch_context)
                masks = private_ane_forward_mask_core_batch_layerwise(model, [item[0] for item in stft_items])
                _private_ane_trace_event(
                    "mask_batch_done",
                    cache_handles=_runner_cache_counts(getattr(model, "_private_ane_runner", None)),
                    **batch_context,
                )
                batch_summary = dict(getattr(model, "_pymss_private_ane_last_summary", {}) or {})
                for sample in batch_summary.get("memory_samples") or ():
                    sample = dict(sample)
                    for key, value in batch_context.items():
                        sample.setdefault(key, value)
                    memory_samples.append(sample)
                batch_summary.pop("memory_samples", None)
                private_ane_batch_summaries.append(batch_summary)
                if defer_istft_until_after_masks:
                    pending_istft_items.extend(
                        (mask, stft_item)
                        for mask, stft_item in zip(masks, stft_items, strict=True)
                    )
                    sample_memory("after_deferred_mask_batch", batch_index)
                else:
                    if _private_ane_bool_config(config.inference.get("private_ane_release_aux_handles_before_istft", True)):
                        runner = getattr(model, "_private_ane_runner", None)
                        cache_handles = _runner_cache_counts(runner) or {}
                        if (
                                runner is not None
                                and hasattr(runner, "clear_aux_handle_cache")
                                and int(cache_handles.get("aux_handles", 0) or 0) > 0
                        ):
                            release_runner_cache(
                                "aux_cache_release_before_istft",
                                batch_index,
                                "clear_aux_handle_cache",
                                batch_context,
                            )
                            aux_cache_releases += 1
                    for mask, (stft_repr, context, window, start, length) in zip(masks, stft_items, strict=True):
                        _private_ane_trace_event(
                            "istft_start",
                            batch=int(batch_index),
                            chunk_start=int(start),
                            chunk_valid_length=int(length),
                        )
                        stft_complex = torch.view_as_complex(stft_repr.unsqueeze(1).contiguous())
                        mask_complex = torch.view_as_complex(mask.contiguous()).type(stft_complex.dtype)
                        istft_started = time.perf_counter()
                        output = private_ane_istft_roformer(model, stft_complex * mask_complex, context, context.audio_length).float()
                        _private_ane_trace_event(
                            "istft_done",
                            batch=int(batch_index),
                            chunk_start=int(start),
                            wall_sec=float(time.perf_counter() - istft_started),
                        )
                        istft_summary = getattr(model, "_pymss_private_ane_last_istft", {}) or {}
                        istft_summary = dict(istft_summary)
                        istft_summary["wall_sec"] = float(time.perf_counter() - istft_started)
                        private_ane_istft_summaries.append(istft_summary)
                        if output.ndim == 3:
                            output = output.unsqueeze(1)
                        output = _select_sources(output.cpu(), source_indices)
                        _add_weighted_chunk(result, counter, output[0], window, start, length)
                        progress.update(step)
                        del mask, stft_repr, context, stft_complex, mask_complex, output

                    runner = getattr(model, "_private_ane_runner", None)
                    cache_handles = _runner_cache_counts(runner) or {}
                    if (
                            runner is not None
                            and hasattr(runner, "clear_irfft_cache")
                            and int(cache_handles.get("irfft_handles", 0) or 0) > 0
                    ):
                        release_runner_cache("irfft_cache_release", batch_index, "clear_irfft_cache", batch_context)
                        irfft_cache_releases += 1

                del masks, stft_items
                batch_memory_release = _release_private_ane_batch_memory()
                cache_release_events.append({
                    "label": "release_private_ane_batch_memory",
                    "batch": int(batch_index),
                    "method": "_release_private_ane_batch_memory",
                    "summary": batch_memory_release,
                    **batch_context,
                })
                _private_ane_trace_event(
                    "release_private_ane_batch_memory_done",
                    wall_sec=batch_memory_release.get("wall_sec"),
                    gc_sec=batch_memory_release.get("gc_sec"),
                    mps_empty_cache_sec=batch_memory_release.get("mps_empty_cache_sec"),
                    **batch_context,
                )
                runner = getattr(model, "_private_ane_runner", None)
                clear_transformer_after_batch = (
                    transformer_cache_segments > 0
                    and transformer_cache_segments_mode != "explicit"
                )
                if runner is not None:
                    cache_handles = _runner_cache_counts(runner) or {}
                    preserve_aux_handles = runner_preserves_aux_handles(runner)
                    preserve_stft_handles = runner_preserves_stft_handles(runner)
                    clear_non_transformer_after_batch = should_release_non_transformer_handles(
                        cache_handles,
                        preserve_aux_handles,
                        preserve_stft_handles,
                    )
                    release_method = (
                        "clear_cache" if clear_transformer_after_batch else "clear_non_transformer_cache"
                    )
                    if (clear_transformer_after_batch or clear_non_transformer_after_batch) and hasattr(runner, release_method):
                        release_kwargs = {}
                        if release_method in ("clear_cache", "clear_non_transformer_cache"):
                            release_kwargs["preserve_aux_handles"] = preserve_aux_handles
                            release_kwargs["preserve_stft_handles"] = preserve_stft_handles
                        release_runner_cache(
                            "batch_cache_release",
                            batch_index,
                            release_method,
                            batch_context,
                            release_kwargs,
                        )
                        batch_cache_releases += 1
                        if clear_transformer_after_batch:
                            transformer_cache_releases += 1
                    after_batch_context = dict(batch_context)
                    cache_handles = _runner_cache_counts(runner)
                    if cache_handles is not None:
                        after_batch_context["cache_handles"] = cache_handles
                    sample_memory("after_batch", batch_index, after_batch_context)
                else:
                    sample_memory("after_batch", batch_index, batch_context)
                if runner is not None:
                    runner.memory_context = {}
                _private_ane_trace_event(
                    "batch_done",
                    cache_handles=_runner_cache_counts(runner),
                    **batch_context,
                )

            if defer_istft_until_after_masks:
                if _private_ane_bool_config(config.inference.get("private_ane_release_aux_handles_before_istft", True)):
                    runner = getattr(model, "_private_ane_runner", None)
                    if runner is not None and hasattr(runner, "clear_aux_handle_cache"):
                        release_runner_cache(
                            "deferred_aux_cache_release",
                            0,
                            "clear_aux_handle_cache",
                            {"deferred_istft": True},
                        )
                        aux_cache_releases += 1
                for pending_index, (mask, (stft_repr, context, window, start, length)) in enumerate(pending_istft_items):
                    _private_ane_trace_event(
                        "deferred_istft_start",
                        pending_index=int(pending_index),
                        chunk_start=int(start),
                        chunk_valid_length=int(length),
                    )
                    stft_complex = torch.view_as_complex(stft_repr.unsqueeze(1).contiguous())
                    mask_complex = torch.view_as_complex(mask.contiguous()).type(stft_complex.dtype)
                    istft_started = time.perf_counter()
                    output = private_ane_istft_roformer(model, stft_complex * mask_complex, context, context.audio_length).float()
                    _private_ane_trace_event(
                        "deferred_istft_done",
                        pending_index=int(pending_index),
                        chunk_start=int(start),
                        wall_sec=float(time.perf_counter() - istft_started),
                    )
                    istft_summary = getattr(model, "_pymss_private_ane_last_istft", {}) or {}
                    istft_summary = dict(istft_summary)
                    istft_summary["wall_sec"] = float(time.perf_counter() - istft_started)
                    private_ane_istft_summaries.append(istft_summary)
                    if output.ndim == 3:
                        output = output.unsqueeze(1)
                    output = _select_sources(output.cpu(), source_indices)
                    _add_weighted_chunk(result, counter, output[0], window, start, length)
                    progress.update(step)
                    runner = getattr(model, "_private_ane_runner", None)
                    if runner is not None and hasattr(runner, "clear_irfft_cache"):
                        release_runner_cache(
                            "deferred_irfft_cache_release",
                            pending_index,
                            "clear_irfft_cache",
                            {"deferred_istft": True, "pending_index": int(pending_index)},
                        )
                        irfft_cache_releases += 1
                    del mask, stft_repr, context, stft_complex, mask_complex, output
                    batch_memory_release = _release_private_ane_batch_memory()
                    cache_release_events.append({
                        "label": "deferred_release_private_ane_batch_memory",
                        "batch": int(pending_index),
                        "method": "_release_private_ane_batch_memory",
                        "summary": batch_memory_release,
                        "deferred_istft": True,
                        "pending_index": int(pending_index),
                    })
                    _private_ane_trace_event(
                        "deferred_release_private_ane_batch_memory_done",
                        pending_index=int(pending_index),
                        wall_sec=batch_memory_release.get("wall_sec"),
                        gc_sec=batch_memory_release.get("gc_sec"),
                        mps_empty_cache_sec=batch_memory_release.get("mps_empty_cache_sec"),
                    )
                pending_istft_items.clear()

            if private_ane_batch_summaries:
                stage_metadata_keys = {
                    "tile_seq",
                    "out_tile",
                    "frame_tile",
                    "frames",
                    "stage",
                    "batch_channels",
                    "input_target_max",
                    "input_prescale",
                    "rmsnorm",
                    "fused",
                    "fused_layout",
                    "fused_groups",
                    "fused_max_outputs",
                    "dynamic_groups",
                    "dynamic_out_ch",
                    "dynamic_computed_out_ch",
                    "dynamic_zero_rows",
                    "dynamic_compact_rows",
                    "max_outputs_per_group",
                    "outputs",
                    "hot_gc_interval",
                    "guard_interval",
                }

                def sum_stage(stage_name):
                    total = {}
                    for summary in private_ane_batch_summaries:
                        stage = summary.get(stage_name) or {}
                        for key, value in stage.items():
                            if key in stage_metadata_keys or isinstance(value, bool):
                                total[key] = value
                            elif isinstance(value, (int, float)):
                                total[key] = float(total.get(key, 0.0) or 0.0) + float(value)
                            else:
                                total[key] = value
                    return total

                def sum_stage_items(items):
                    total = {}
                    for stage in items:
                        for key, value in dict(stage or {}).items():
                            if key in stage_metadata_keys or isinstance(value, bool):
                                total[key] = value
                            elif isinstance(value, (int, float)):
                                total[key] = float(total.get(key, 0.0) or 0.0) + float(value)
                            else:
                                total[key] = value
                    return total

                band_split = sum_stage("band_split")
                final_norm = sum_stage("final_norm")
                mask = sum_stage("mask")
                mask_batch_detail = sum_stage("mask_batch_detail")
                transformer_detail = sum_stage("transformer_detail")
                stft = sum_stage_items(private_ane_stft_summaries)
                istft = sum_stage_items(private_ane_istft_summaries)
                transformer_compile_sec = 0.0
                transformer_eval_sec = 0.0
                transformer_cache_hits = 0
                transformer_cache_kept = 0
                bridge_load_cache_hits = 0
                bridge_load_cache_misses = 0
                bridge_load_cache_enabled = False
                transformer_profile_skip_keys = {"layer", "eval_sec"}
                transformer_by_axis = {}
                transformer_timings_tail = deque(maxlen=transformer_timing_tail_limit)
                transformer_timing_count = 0
                for batch_summary_index, summary in enumerate(private_ane_batch_summaries):
                    bridge_cache = summary.get("bridge_load_cache") or {}
                    bridge_load_cache_enabled = bridge_load_cache_enabled or bool(bridge_cache.get("enabled"))
                    bridge_load_cache_hits += int(bridge_cache.get("hits", 0) or 0)
                    bridge_load_cache_misses += int(bridge_cache.get("misses", 0) or 0)
                    for timing in summary.get("transformer_timings") or ():
                        transformer_timing_count += 1
                        timing_row = dict(timing)
                        timing_row["batch_summary_index"] = int(batch_summary_index)
                        transformer_timings_tail.append(timing_row)
                        axis = timing.get("axis", "unknown")
                        axis_row = transformer_by_axis.setdefault(
                            axis,
                            {"compile_sec": 0.0, "eval_sec": 0.0, "segments": 0, "cache_hits": 0, "cache_kept": 0},
                        )
                        compile_sec = float(timing.get("compile_wall_sec", 0.0) or 0.0)
                        eval_sec = float(timing.get("eval_sec", 0.0) or 0.0)
                        transformer_compile_sec += compile_sec
                        transformer_eval_sec += eval_sec
                        axis_row["compile_sec"] += compile_sec
                        axis_row["eval_sec"] += eval_sec
                        axis_row["segments"] += 1
                        if timing.get("cache_hit"):
                            transformer_cache_hits += 1
                            axis_row["cache_hits"] += 1
                        if timing.get("cache_kept"):
                            transformer_cache_kept += 1
                            axis_row["cache_kept"] += 1
                        for key, value in timing.items():
                            if (
                                key not in transformer_profile_skip_keys
                                and isinstance(value, (int, float))
                                and not isinstance(value, bool)
                            ):
                                axis_row[key] = axis_row.get(key, 0.0) + float(timing.get(key, 0.0) or 0.0)
                memory_samples_tail = list(memory_samples)
                runner = getattr(model, "_private_ane_runner", None)
                final_cache_handles = _runner_cache_counts(runner)
                cache_release_tail = cache_release_events[-PRIVATE_ANE_MEMORY_TAIL_SAMPLES:]
                free_profile_by_family = dict(getattr(runner, "_free_profile_by_family", {}) or {}) if runner is not None else {}
                model._pymss_private_ane_last_summary = {
                    "transformer_sec": float(sum(float(s.get("transformer_sec", 0.0) or 0.0) for s in private_ane_batch_summaries)),
                    "gelu_mode": getattr(model, "private_ane_gelu_mode", "EXACT"),
                    "fuse_residual": bool(getattr(model, "private_ane_fuse_residual", True)),
                    "fuse_gate_ffn": bool(getattr(model, "private_ane_fuse_gate_ffn", False)),
                    "two_input_gate": bool(getattr(model, "private_ane_two_input_gate", False)),
                    "bridge_pack_gate": bool(getattr(model, "private_ane_bridge_pack_gate", True)),
                    "bridge_wrapper_route": _private_ane_bool_config(
                        getattr(model, "private_ane_bridge_wrapper_route", False)
                    ),
                    "surface_handoff_gate_ffn": bool(
                        getattr(model, "private_ane_surface_handoff_gate_ffn", False)
                    ),
                    "persistent_transformer_handles": _private_ane_bool_config(
                        getattr(model, "private_ane_persistent_transformer_handles", False)
                    ),
                    "allow_transformer_handle_cache": _private_ane_bool_config(
                        getattr(model, "private_ane_allow_transformer_handle_cache", False)
                    ),
                    "batch_axis_eval": _private_ane_bool_config(
                        getattr(model, "private_ane_batch_axis_eval", False)
                    ),
                    "tiled_time_attention_pre": _private_ane_bool_config(
                        getattr(model, "private_ane_tiled_time_attention_pre", False)
                    ),
                    "tiled_time_attention_pre_q_chunk": int(
                        getattr(model, "private_ane_tiled_time_attention_pre_q_chunk", 128) or 128
                    ),
                    "torch_fallback_allowed": _private_ane_bool_config(
                        getattr(model, "private_ane_allow_torch_fallback", False)
                    ),
                    "release_aux_handles_before_istft": _private_ane_bool_config(
                        config.inference.get("private_ane_release_aux_handles_before_istft", True)
                    ),
                    "dynamic_stft": _private_ane_bool_config_or_model(
                        config, model, "private_ane_dynamic_stft", False
                    ),
                    "dynamic_stft_max_outputs": int(
                        _private_ane_config_or_model(
                            config, model, "private_ane_dynamic_stft_max_outputs", 2048
                        )
                        or 2048
                    ),
                    "fused_stft": _private_ane_bool_config_or_model(
                        config, model, "private_ane_fused_stft", False
                    ),
                    "fused_stft_max_outputs": int(
                        _private_ane_config_or_model(
                            config, model, "private_ane_fused_stft_max_outputs", 17
                        )
                        or 17
                    ),
                    "persistent_stft_handles": _private_ane_bool_config_or_model(
                        config, model, "private_ane_persistent_stft_handles", False
                    ),
                    "preload_stft_handles": _private_ane_bool_config_or_model(
                        config, model, "private_ane_preload_stft_handles", False
                    ),
                    "defer_istft_until_after_masks": bool(defer_istft_until_after_masks),
                    "stft_cache_releases": int(stft_cache_releases),
                    "irfft_cache_releases": int(irfft_cache_releases),
                    "aux_cache_releases": int(aux_cache_releases),
                    "batch_cache_releases": int(batch_cache_releases),
                    "transformer_cache_releases": int(transformer_cache_releases),
                    "cache_releases": {
                        "event_count": int(len(cache_release_events)),
                        "tail_count": int(len(cache_release_tail)),
                        "events": cache_release_tail,
                    },
                    "free_profile_by_family": free_profile_by_family,
                    "final_cache_handles": final_cache_handles,
                    "stft_istft_batch_channels": _private_ane_bool_config_or_model(
                        config, model, "private_ane_stft_istft_batch_channels", False
                    ),
                    "fused_band_split": bool(private_ane_batch_summaries[-1].get("fused_band_split", False)),
                    "fused_mask_estimator": bool(
                        private_ane_batch_summaries[-1].get("fused_mask_estimator", False)
                    ),
                    "gpu_final_norm_mask": bool(
                        private_ane_batch_summaries[-1].get("gpu_final_norm_mask", False)
                    ),
                    "gpu_istft": _private_ane_bool_config(
                        getattr(model, "private_ane_gpu_istft", False)
                    ),
                    "outer_stages": private_ane_batch_summaries[-1].get("outer_stages"),
                    "schedule": "chunk_batches_layerwise_many",
                    "chunks": len(starts),
                    "chunk_batch_size": chunk_batch_size,
                    "chunk_batch_size_mode": chunk_batch_size_mode,
                    "chunk_batch_auto": chunk_batch_auto,
                    "batches": len(private_ane_batch_summaries),
                    "transformer_compile_sec": float(transformer_compile_sec),
                    "transformer_eval_sec": float(transformer_eval_sec),
                    "transformer_cache_hits": int(transformer_cache_hits),
                    "transformer_cache_kept": int(transformer_cache_kept),
                    "transformer_cache_segments": int(transformer_cache_segments or 0),
                    "transformer_cache_segments_mode": transformer_cache_segments_mode,
                    "transformer_cache_auto": transformer_cache_auto,
                    "bridge_load_cache": {
                        "enabled": bool(bridge_load_cache_enabled),
                        "hits": int(bridge_load_cache_hits),
                        "misses": int(bridge_load_cache_misses),
                    },
                    "transformer_by_axis": transformer_by_axis,
                    "transformer_timings": list(transformer_timings_tail),
                    "transformer_timing_count": int(transformer_timing_count),
                    "transformer_timing_tail_count": len(transformer_timings_tail),
                    "transformer_timing_tail_limit": transformer_timing_tail_limit,
                    "band_split": band_split,
                    "final_norm": final_norm,
                    "mask": mask,
                    "mask_batch_detail": mask_batch_detail,
                    "transformer_detail": transformer_detail,
                    "stft_preload": stft_preload_timing,
                    "stft": stft,
                    "istft": istft,
                    "memory": {
                        "max_rss_mb": max_observed_rss_mb,
                        "min_free_memory_percent": min_observed_free_memory_percent,
                        "max_ane_service_rss_mb": (
                            max_observed_ane_service_rss_mb
                        ),
                        "max_swap_used_mb": max_observed_swap_used_mb,
                        "samples": memory_samples_tail,
                        "sample_count": memory_sample_count,
                        "rss_limit_mb": max_rss_mb,
                        "free_memory_percent_limit": min_free_memory_percent,
                        "emergency_free_memory_percent": emergency_free_memory_percent,
                        "free_memory_strikes_limit": free_memory_strikes_limit,
                        "ane_service_rss_limit_mb": max_ane_service_rss_mb,
                        "swap_used_limit_mb": max_swap_used_mb,
                    },
                }

    finally:
        model.private_ane_transformer_cache_segments = original_transformer_cache_segments

    progress.close()
    progress.emit(mix.shape[1])
    return _sources_to_dict(config, _finalize_overlap(result, counter, length_init, border), source_indices)


def demix_track_mlx_full(config, model, mix, device, pbar=False, source_indices=None, progress_callback=None):
    import mlx.core as mx

    C = config.audio.chunk_size
    source_indices = _normalize_source_indices(config, source_indices)
    step = _get_inference_step(config, C)
    border = C - step
    fade_size = min(C // 10, border)
    batch_size = config.inference.batch_size

    mix, length_init = _mlx_prepare_mix_for_chunks(mix, border)
    starts, windows = _mlx_build_chunk_plan(mix.shape[1], C, step, fade_size)
    result = mx.zeros((_source_count(config, source_indices), mix.shape[0], mix.shape[1]), dtype=mx.float32)
    counter = mx.zeros((1, 1, mix.shape[1]), dtype=mx.float32)
    progress = _ProgressContext(pbar, mix.shape[1], progress_callback)

    for batch_start in range(0, len(starts), batch_size):
        batch_indices = range(batch_start, min(batch_start + batch_size, len(starts)))
        batch = [(_mlx_extract_chunk(mix, starts[idx], C), idx) for idx in batch_indices]
        chunks = _mlx_run_model_chunk(model, mx.stack([chunk for (chunk, _), _ in batch], axis=0), C)
        chunks = _mlx_select_sources(chunks, source_indices)
        for j, ((_, length), idx) in enumerate(batch):
            result, counter = _mlx_add_weighted_chunk(result, counter, chunks[j], windows[idx], starts[idx], length)
        mx.eval(result, counter)
        progress.update(step * len(batch))

    progress.close()
    progress.emit(mix.shape[1])
    return _sources_to_dict(config, _mlx_finalize_overlap(result, counter, length_init, border), source_indices)


demix_track_mlx_roformer = demix_track_mlx_full


def demix_track(config, model, mix, device, pbar=False, source_indices=None, progress_callback=None):
    C = config.audio.chunk_size
    source_indices = _normalize_source_indices(config, source_indices)
    step = _get_inference_step(config, C)
    border = C - step
    fade_size = min(C // 10, border)
    batch_size = config.inference.batch_size

    mix, length_init = _prepare_mix_for_chunks(mix, border)
    chunk_starts, chunk_windows = _build_chunk_plan(mix.shape[1], C, step, fade_size)
    device_type = torch.device(device).type
    use_complete_fast_path = device_type in ('cuda', 'cpu')
    mix_device = _model_mix(mix, device)

    with _autocast(device, config.training.get('use_amp', True)):
        with torch.inference_mode():
            result, counter = _init_overlap_buffers(config, mix, device, use_complete_fast_path, source_indices)
            progress = _ProgressContext(pbar, mix.shape[1], progress_callback)

            with _model_source_context(model, source_indices):
                complete_chunks = 0
                if use_complete_fast_path:
                    complete_chunks = _run_complete_chunks(
                        model,
                        mix_device,
                        chunk_windows,
                        result,
                        counter,
                        C,
                        step,
                        batch_size,
                        progress,
                        source_indices,
                    )

                _run_tail_chunks(
                    model,
                    mix_device,
                    chunk_starts,
                    chunk_windows,
                    result,
                    counter,
                    C,
                    step,
                    batch_size,
                    complete_chunks,
                    progress,
                    source_indices,
                )
                progress.emit(mix.shape[1])


            progress.close()

            estimated_sources = _finalize_overlap(result, counter, length_init, border)

    return _sources_to_dict(config, estimated_sources, source_indices)


def demix_track_demucs(config, model, mix, device, pbar=False, source_indices=None, progress_callback=None):
    if _can_demix_mlx_full(model, device):
        return demix_track_mlx_full(config, model, mix.cpu().numpy(), device, pbar=pbar, source_indices=source_indices, progress_callback=progress_callback)

    source_indices = _normalize_source_indices(config, source_indices)
    source_names = _source_names(config)
    S = len(source_names)
    C = config.training.samplerate * config.training.segment
    batch_size = config.inference.batch_size
    step = _get_inference_step(config, C)

    with _autocast(device, config.training.get('use_amp', True)):
        with torch.inference_mode():
            req_shape = (_source_count(config, source_indices), ) + tuple(mix.shape)
            result = torch.zeros(req_shape, dtype=torch.float32)
            counter = torch.zeros(req_shape, dtype=torch.float32)
            i = 0
            batch_data = []
            batch_locations = []
            progress = _ProgressContext(pbar, mix.shape[1], progress_callback)

            while i < mix.shape[1]:
                part = mix[:, i:i + C].to(device)
                length = part.shape[-1]
                if length < C:
                    part = nn.functional.pad(input=part, pad=(0, C - length, 0, 0), mode='constant', value=0)
                batch_data.append(part)
                batch_locations.append((i, length))
                i += step


                if len(batch_data) >= batch_size or (i >= mix.shape[1]):
                    arr = torch.stack(batch_data, dim=0)
                    x = _select_sources(model(arr), source_indices)
                    for j, (start, l) in enumerate(batch_locations):
                        result[..., start:start+l] += x[j][..., :l].cpu()
                        counter[..., start:start+l] += 1.
                    batch_data, batch_locations = [], []

                if progress.bar:
                    progress.bar.update(step)
                progress.emit(min(i, mix.shape[1]))

            progress.close()
            progress.emit(mix.shape[1])

            estimated_sources = (result / counter).cpu().numpy()
            np.nan_to_num(estimated_sources, copy=False, nan=0.0)

    if S == 1 and source_indices is None:
        return estimated_sources
    return _sources_to_dict(config, estimated_sources, source_indices)

def demix(config, model, mix: NDArray, device, pbar=False, model_type: str = None, source_indices=None, progress_callback=None) -> Dict[str, NDArray]:
    if _can_demix_private_ane(model, device):
        return demix_track_private_ane(config, model, mix, device, pbar=pbar, source_indices=source_indices, progress_callback=progress_callback)
    if _can_demix_coreml_ane_segmented(model, device):
        return demix_track_coreml_ane_segmented(config, model, mix, device, pbar=pbar, source_indices=source_indices, progress_callback=progress_callback)
    if _can_demix_mlx_full(model, device):
        return demix_track_mlx_full(config, model, mix, device, pbar=pbar, source_indices=source_indices, progress_callback=progress_callback)
    mix = torch.tensor(mix, dtype=torch.float32)
    if model_type in {'demucs', 'tasnet', 'legacy_demucs', 'legacy_tasnet'}:
        from .modules.legacy_demucs import apply_legacy_model

        progress = _ProgressContext(callback=progress_callback)
        progress.emit(0)
        with _autocast(device, config.training.get('use_amp', True)):
            with torch.inference_mode():
                estimates = apply_legacy_model(
                    model,
                    mix.to(device),
                    shifts=int(config.inference.get('shifts', 0)),
                    split=bool(config.inference.get('split', True)),
                    overlap=float(config.inference.get('overlap', 0.25)),
                    progress=pbar,
                ).cpu().numpy()
        progress.emit(1)
        return dict(zip(config.training.instruments, estimates))
    if model_type == 'htdemucs':
        return demix_track_demucs(config, model, mix, device, pbar=pbar, source_indices=source_indices, progress_callback=progress_callback)
    return demix_track(config, model, mix, device, pbar=pbar, source_indices=source_indices, progress_callback=progress_callback)
