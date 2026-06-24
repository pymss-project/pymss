from __future__ import annotations

import gc
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .common import SpectralContext, mask_to_complex_shape


REPO_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = REPO_ROOT / "benchmark"
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

from private_ane_real_attention_probe import ANEBridge, DIM, HD, HEADS, INNER, _blob  # noqa: E402
from private_ane_real_attention_split_probe import _attention_pre_mil, _pre_weights  # noqa: E402
from private_ane_real_block_probe import _block_modules, _compile_block, _run_block  # noqa: E402


TIME_SEQ = 938
TIME_PAD = 960
FREQ_SEQ = 62
FREQ_PAD = 64
INPUT_DIM = 4100
BAND_COUNT = 62
MASK_DIM = 4100
TILE_SEQ = 64
BAND_INPUT_TARGET_MAX = 8.0
FUSED_BAND_SPLIT_MAX_OUTPUTS = 4
FUSED_MASK_MAX_OUTPUTS = 8
FFN_HIDDEN = 1024
MASK_HIDDEN = 1024
STFT_N_FFT = 2048
STFT_HOP = 512
STFT_FREQ_BINS = STFT_N_FFT // 2 + 1
STFT_OUT_TILE = 128
STFT_FRAME_TILE = 512
ISTFT_OUT_TILE = 128
ISTFT_FRAME_TILE = 64
BRIDGE_PROFILE_TIME_KEYS = (
    "total_sec",
    "mil_data_sec",
    "weights_dict_sec",
    "descriptor_sec",
    "model_create_sec",
    "identifier_sec",
    "tmpdir_sec",
    "file_write_sec",
    "compile_qos_sec",
    "load_qos_sec",
    "surface_create_sec",
    "request_create_sec",
    "handle_create_sec",
    "eval_total_sec",
    "setup_sec",
    "send_sec",
    "eval_client_sec",
    "eval_client_setup_sec",
    "eval_client_send_sec",
    "eval_direct_process_sec",
    "eval_direct_process_setup_sec",
    "eval_direct_process_send_sec",
    "eval_model_sec",
    "eval_model_setup_sec",
    "eval_model_send_sec",
)
DEFAULT_PRIVATE_ANE_MAX_RSS_MB = 1792.0
DEFAULT_PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT = 0
DEFAULT_PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT = 0
DEFAULT_PRIVATE_ANE_MAX_ANE_SERVICE_RSS_MB = 512.0
DEFAULT_PRIVATE_ANE_MAX_SWAP_USED_MB = 0.0
DEFAULT_PRIVATE_ANE_FREE_MEMORY_STRIKES = 3
DEFAULT_PRIVATE_ANE_STFT_BRIDGE_QOS = 25
DEFAULT_PRIVATE_ANE_STFT_CACHE_TMPDIR = "/tmp/pymss_private_ane_stft_loadcache"
DEFAULT_PRIVATE_ANE_TRANSFORMER_HOT_GC_INTERVAL = 0
DEFAULT_PRIVATE_ANE_TRANSFORMER_GUARD_INTERVAL = 0
MIN_PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT = 30
MIN_PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT = 30
MAX_PRIVATE_ANE_MAX_SWAP_USED_MB = 1536.0
MAX_MEMORY_SAMPLES = 128


@contextmanager
def _temporary_env_value(name: str, value: object | None, *, clear_if_none: bool = False):
    if value is None and not clear_if_none:
        yield
        return
    previous = os.environ.get(name)
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = str(value)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def _optional_float(value, default):
    if value in (None, "", 0, "0"):
        return None
    if value == "default":
        return default
    return float(value)


def _optional_int(value, default):
    if value in (None, "", 0, "0"):
        return None
    if value == "default":
        return default
    return int(value)


def _accumulate_bridge_profile_totals(total: dict[str, float], profile: dict[str, object]) -> None:
    for key in BRIDGE_PROFILE_TIME_KEYS:
        out_key = f"bridge_profile_{key}"
        total[out_key] = float(total.get(out_key, 0.0) or 0.0) + float(profile.get(out_key, 0.0) or 0.0)
    for key in ("fast_load_attempted", "fast_load_hit", "fast_load_fallback", "keep_tmpdir"):
        out_key = f"bridge_profile_{key}"
        total[out_key] = float(total.get(out_key, 0.0) or 0.0) + float(profile.get(out_key, 0.0) or 0.0)
    for key in ("route", "identifier", "tmp_dir", "client_file_error"):
        value = profile.get(f"bridge_profile_{key}")
        if value:
            total[f"bridge_profile_{key}"] = str(value)


def _bridge_compile_profile_from_bridge(bridge, elapsed_sec: float, *, handle_cache_hit: bool = False) -> dict[str, object]:
    if handle_cache_hit:
        out = {
            "route": "handle_cache",
            "handle_cache_hit": True,
            "load_cache_attempted": False,
            "load_cache_hit": False,
            "compile_sec": 0.0,
            "cold_compile_sec": 0.0,
            "load_cache_sec": 0.0,
            "load_cache_attempt_sec": 0.0,
            "load_cache_miss_sec": 0.0,
            "load_or_compile_sec": 0.0,
            "bridge_load_or_compile_sec": 0.0,
        }
        for key in BRIDGE_PROFILE_TIME_KEYS:
            out[f"bridge_profile_{key}"] = 0.0
        return out
    route = str(getattr(bridge, "last_compile_route", "unknown") or "unknown")
    load_cache_attempted = bool(getattr(bridge, "last_load_cache_attempted", False))
    load_cache_hit = bool(getattr(bridge, "last_load_cache_hit", False))
    load_cache_attempt_sec = float(getattr(bridge, "last_load_cache_sec", 0.0) or 0.0)
    cold_compile_sec = float(getattr(bridge, "last_cold_compile_sec", 0.0) or 0.0)
    bridge_total_sec = float(getattr(bridge, "last_compile_total_sec", 0.0) or 0.0)
    native_profile = getattr(bridge, "last_bridge_profile", {}) or {}
    out = {
        "route": route,
        "handle_cache_hit": False,
        "load_cache_attempted": load_cache_attempted,
        "load_cache_hit": load_cache_hit,
        "compile_sec": cold_compile_sec,
        "cold_compile_sec": cold_compile_sec,
        "load_cache_sec": load_cache_attempt_sec if load_cache_hit else 0.0,
        "load_cache_attempt_sec": load_cache_attempt_sec,
        "load_cache_miss_sec": load_cache_attempt_sec if load_cache_attempted and not load_cache_hit else 0.0,
        "load_or_compile_sec": float(elapsed_sec),
        "bridge_load_or_compile_sec": bridge_total_sec,
    }
    for key in BRIDGE_PROFILE_TIME_KEYS:
        out[f"bridge_profile_{key}"] = float(native_profile.get(key, 0.0) or 0.0)
    out["bridge_profile_success"] = bool(native_profile.get("success", False))
    out["bridge_profile_n_weights"] = int(native_profile.get("n_weights", 0) or 0)
    out["bridge_profile_n_inputs"] = int(native_profile.get("n_inputs", 0) or 0)
    out["bridge_profile_n_outputs"] = int(native_profile.get("n_outputs", 0) or 0)
    out["bridge_profile_fast_load_attempted"] = int(native_profile.get("fast_load_attempted", 0) or 0)
    out["bridge_profile_fast_load_hit"] = int(native_profile.get("fast_load_hit", 0) or 0)
    out["bridge_profile_fast_load_fallback"] = int(native_profile.get("fast_load_fallback", 0) or 0)
    out["bridge_profile_keep_tmpdir"] = int(native_profile.get("keep_tmpdir", 0) or 0)
    out["bridge_profile_route"] = str(native_profile.get("route", "") or "")
    out["bridge_profile_identifier"] = str(native_profile.get("identifier", "") or "")
    out["bridge_profile_tmp_dir"] = str(native_profile.get("tmp_dir", "") or "")
    out["bridge_profile_client_file_attempted"] = int(native_profile.get("client_file_attempted", 0) or 0)
    out["bridge_profile_client_file_loaded"] = int(native_profile.get("client_file_loaded", 0) or 0)
    out["bridge_profile_client_file_error"] = str(native_profile.get("client_file_error", "") or "")
    return out


def _accumulate_named_bridge_compile_profiles(
        total: dict[str, object],
        profiles: dict[str, dict[str, object]],
) -> None:
    for name, profile in profiles.items():
        if not profile:
            continue
        _accumulate_bridge_profile_totals(total, profile)
        for key in ("route", "identifier", "tmp_dir", "client_file_error"):
            value = profile.get(f"bridge_profile_{key}", profile.get(key))
            if value:
                total[f"{name}_bridge_profile_{key}"] = str(value)
        for key in BRIDGE_PROFILE_TIME_KEYS:
            total[f"{name}_bridge_profile_{key}"] = float(
                profile.get(f"bridge_profile_{key}", profile.get(key, 0.0)) or 0.0
            )
        for key in ("fast_load_attempted", "fast_load_hit", "fast_load_fallback", "keep_tmpdir"):
            total[f"{name}_bridge_profile_{key}"] = int(
                profile.get(f"bridge_profile_{key}", profile.get(key, 0)) or 0
            )


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


def _conv_consts() -> str:
    return """
        string pt = const()[name = string("pt"), val = string("valid")];
        tensor<int32, [2]> st = const()[name = string("st"), val = tensor<int32, [2]>([1, 1])];
        tensor<int32, [4]> pd = const()[name = string("pd"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [2]> dl = const()[name = string("dl"), val = tensor<int32, [2]>([1, 1])];
        int32 gr = const()[name = string("gr"), val = int32(1)];"""


def _rms_norm_mil_expr(name: str, x_name: str, batch: int, channels: int, seq: int, gamma_path: str) -> str:
    inv = 1.0 / float(channels)
    return f"""
        tensor<fp16, [1, {channels}, 1, 1]> {name}_gamma = const()[name = string("{name}_gamma"), val = tensor<fp16, [1, {channels}, 1, 1]>(BLOBFILE(path = string("{gamma_path}"), offset = uint64(64)))];
        tensor<fp16, [{batch}, {channels}, 1, {seq}]> {name}_sq = mul(x = {x_name}, y = {x_name})[name = string("{name}_sq")];
        tensor<int32, [1]> {name}_rax = const()[name = string("{name}_rax"), val = tensor<int32, [1]>([1])];
        bool {name}_kd = const()[name = string("{name}_kd"), val = bool(true)];
        tensor<fp16, [{batch}, 1, 1, {seq}]> {name}_ss = reduce_sum(x = {name}_sq, axes = {name}_rax, keep_dims = {name}_kd)[name = string("{name}_ss")];
        fp16 {name}_invd = const()[name = string("{name}_invd"), val = fp16({inv})];
        tensor<fp16, [{batch}, 1, 1, {seq}]> {name}_mean = mul(x = {name}_ss, y = {name}_invd)[name = string("{name}_mean")];
        fp16 {name}_nh = const()[name = string("{name}_nh"), val = fp16(-0.5)];
        tensor<fp16, [{batch}, 1, 1, {seq}]> {name}_rrms = pow(x = {name}_mean, y = {name}_nh)[name = string("{name}_rrms")];
        tensor<fp16, [{batch}, {channels}, 1, {seq}]> {name}_xn = mul(x = {x_name}, y = {name}_rrms)[name = string("{name}_xn")];
        tensor<fp16, [{batch}, {channels}, 1, {seq}]> {name}_out = mul(x = {name}_xn, y = {name}_gamma)[name = string("{name}_out")];"""


def _fused_gate_ffn_mil(batch: int, seq: int, gelu_mode: str) -> str:
    packed = DIM + INNER
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {packed}, 1, {seq}]> packed) {{
{_conv_consts()}
        tensor<int32, [4]> xb = const()[name = string("xb"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [4]> xe = const()[name = string("xe"), val = tensor<int32, [4]>([{batch}, {DIM}, 1, {seq}])];
        tensor<int32, [4]> ab = const()[name = string("ab"), val = tensor<int32, [4]>([0, {DIM}, 0, 0])];
        tensor<int32, [4]> ae = const()[name = string("ae"), val = tensor<int32, [4]>([{batch}, {packed}, 1, {seq}])];
        tensor<bool, [4]> sm = const()[name = string("sm"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> ss0 = const()[name = string("ss0"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [{batch}, {DIM}, 1, {seq}]> x = slice_by_index(begin = xb, end = xe, end_mask = sm, stride = ss0, x = packed)[name = string("x")];
        tensor<fp16, [{batch}, {INNER}, 1, {seq}]> att_flat = slice_by_index(begin = ab, end = ae, end_mask = sm, stride = ss0, x = packed)[name = string("att_flat")];

{_rms_norm_mil_expr("att_norm", "x", batch, DIM, seq, "@model_path/weights/att_gamma.bin")}
        tensor<fp16, [{HEADS}, {DIM}, 1, 1]> Wg = const()[name = string("Wg"), val = tensor<fp16, [{HEADS}, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/wg.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {HEADS}, 1, 1]> Bg = const()[name = string("Bg"), val = tensor<fp16, [1, {HEADS}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/bg.bin"), offset = uint64(64)))];
        tensor<fp16, [{DIM}, {INNER}, 1, 1]> Wo = const()[name = string("Wo"), val = tensor<fp16, [{DIM}, {INNER}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/wo.bin"), offset = uint64(64)))];
        tensor<fp16, [{batch}, {HEADS}, 1, {seq}]> g0 = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = Wg, x = att_norm_out)[name = string("cg")];
        tensor<fp16, [{batch}, {HEADS}, 1, {seq}]> gb = add(x = g0, y = Bg)[name = string("gb")];
        tensor<fp16, [{batch}, {HEADS}, 1, {seq}]> gs = sigmoid(x = gb)[name = string("sig")];
        tensor<int32, [4]> ash = const()[name = string("ash"), val = tensor<int32, [4]>([{batch}, {HEADS}, {HD}, {seq}])];
        tensor<fp16, [{batch}, {HEADS}, {HD}, {seq}]> att = reshape(shape = ash, x = att_flat)[name = string("att")];
        tensor<fp16, [{batch}, {HEADS}, {HD}, {seq}]> gated = mul(x = att, y = gs)[name = string("gate")];
        tensor<int32, [4]> osh = const()[name = string("osh"), val = tensor<int32, [4]>([{batch}, {INNER}, 1, {seq}])];
        tensor<fp16, [{batch}, {INNER}, 1, {seq}]> flat = reshape(shape = osh, x = gated)[name = string("flat")];
        tensor<fp16, [{batch}, {DIM}, 1, {seq}]> att_delta = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = Wo, x = flat)[name = string("co")];
        tensor<fp16, [{batch}, {DIM}, 1, {seq}]> x2 = add(x = x, y = att_delta)[name = string("att_resid")];

{_rms_norm_mil_expr("ffn_norm", "x2", batch, DIM, seq, "@model_path/weights/ffn_gamma.bin")}
        tensor<fp16, [{FFN_HIDDEN}, {DIM}, 1, 1]> W1 = const()[name = string("W1"), val = tensor<fp16, [{FFN_HIDDEN}, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {FFN_HIDDEN}, 1, 1]> B1 = const()[name = string("B1"), val = tensor<fp16, [1, {FFN_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b1.bin"), offset = uint64(64)))];
        tensor<fp16, [{DIM}, {FFN_HIDDEN}, 1, 1]> W2 = const()[name = string("W2"), val = tensor<fp16, [{DIM}, {FFN_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, 1]> B2 = const()[name = string("B2"), val = tensor<fp16, [1, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b2.bin"), offset = uint64(64)))];
        tensor<fp16, [{batch}, {FFN_HIDDEN}, 1, {seq}]> h1c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W1, x = ffn_norm_out)[name = string("c1")];
        tensor<fp16, [{batch}, {FFN_HIDDEN}, 1, {seq}]> h1 = add(x = h1c, y = B1)[name = string("b1")];
        string gm = const()[name = string("gm"), val = string("{gelu_mode}")];
        tensor<fp16, [{batch}, {FFN_HIDDEN}, 1, {seq}]> h = gelu(mode = gm, x = h1)[name = string("gelu")];
        tensor<fp16, [{batch}, {DIM}, 1, {seq}]> ffn_delta_c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W2, x = h)[name = string("c2")];
        tensor<fp16, [{batch}, {DIM}, 1, {seq}]> ffn_delta = add(x = ffn_delta_c, y = B2)[name = string("b2")];
        tensor<fp16, [{batch}, {DIM}, 1, {seq}]> out = add(x = x2, y = ffn_delta)[name = string("out")];
    }} -> (out);
}}
"""


def _fused_gate_ffn_weights(attn, ffn) -> dict[str, bytes]:
    norm, linear_in, _, _, linear_out, _ = ffn.net
    return {
        "@model_path/weights/att_gamma.bin": _blob(attn.norm.gamma.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/wg.bin": _blob(attn.to_gates.weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/bg.bin": _blob(attn.to_gates.bias.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/wo.bin": _blob(attn.to_out[0].weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/ffn_gamma.bin": _blob(norm.gamma.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/w1.bin": _blob(linear_in.weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/b1.bin": _blob(linear_in.bias.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/w2.bin": _blob(linear_out.weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/b2.bin": _blob(linear_out.bias.detach().cpu().numpy()[None, :, None, None]),
    }


def _compile_fused_gate_ffn_block(
        bridge: ANEBridge,
        attn,
        ffn,
        batch: int,
        seq: int,
        valid_seq: int,
        gelu_mode: str,
        x_bytes: int,
        memory_guard=None,
        attention_pre_mil: str | None = None,
):
    pre = None
    fused = None
    pre_profile: dict[str, object] = {}
    fused_profile: dict[str, object] = {}
    try:
        if memory_guard is not None:
            memory_guard("before_attention_pre_compile")
        started = time.perf_counter()
        pre = bridge.compile(
            attention_pre_mil or _attention_pre_mil(batch, seq, valid_seq),
            _pre_weights(attn, seq, valid_seq),
            x_bytes,
            batch * INNER * seq * 2,
        )
        pre_sec = time.perf_counter() - started
        pre_profile = _bridge_compile_profile_from_bridge(bridge, pre_sec)
        if memory_guard is not None:
            memory_guard("after_attention_pre_compile")

        if memory_guard is not None:
            memory_guard("before_fused_gate_ffn_compile")
        started = time.perf_counter()
        fused = bridge.compile(
            _fused_gate_ffn_mil(batch, seq, gelu_mode),
            _fused_gate_ffn_weights(attn, ffn),
            batch * (DIM + INNER) * seq * 2,
            x_bytes,
        )
        fused_sec = time.perf_counter() - started
        fused_profile = _bridge_compile_profile_from_bridge(bridge, fused_sec)
        if memory_guard is not None:
            memory_guard("after_fused_gate_ffn_compile")
        handles = (pre, fused)
        pre = None
        fused = None
        return handles, (pre_sec, fused_sec, 0.0), {
            "pre": pre_profile,
            "gate": fused_profile,
            "ffn": {},
        }
    finally:
        for handle in (pre, fused):
            if handle is not None:
                bridge.free(handle)


def _band_split_mil(dim_inputs: tuple[int, ...], seq: int = TIME_SEQ) -> str:
    body = [_conv_consts()]
    outputs = []
    offset = 0
    for band_index, dim_in in enumerate(dim_inputs):
        begin = offset
        end = offset + dim_in
        body.append(f"""
        tensor<int32, [4]> b{band_index}_begin = const()[name = string("b{band_index}_begin"), val = tensor<int32, [4]>([0, {begin}, 0, 0])];
        tensor<int32, [4]> b{band_index}_end = const()[name = string("b{band_index}_end"), val = tensor<int32, [4]>([1, {end}, 1, {seq}])];
        tensor<bool, [4]> b{band_index}_mask = const()[name = string("b{band_index}_mask"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> b{band_index}_stride = const()[name = string("b{band_index}_stride"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{band_index}_x = slice_by_index(begin = b{band_index}_begin, end = b{band_index}_end, end_mask = b{band_index}_mask, stride = b{band_index}_stride, x = x)[name = string("b{band_index}_x")];""")
        body.append(_rms_norm_mil_expr(f"b{band_index}_norm", f"b{band_index}_x", 1, dim_in, seq, f"@model_path/weights/b{band_index}_gamma.bin"))
        body.append(f"""
        tensor<fp16, [{DIM}, {dim_in}, 1, 1]> b{band_index}_w = const()[name = string("b{band_index}_w"), val = tensor<fp16, [{DIM}, {dim_in}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{band_index}_w.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, 1]> b{band_index}_bias = const()[name = string("b{band_index}_bias"), val = tensor<fp16, [1, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{band_index}_bias.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, {seq}]> b{band_index}_conv = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = b{band_index}_w, x = b{band_index}_norm_out)[name = string("b{band_index}_conv")];
        tensor<fp16, [1, {DIM}, 1, {seq}]> b{band_index}_out = add(x = b{band_index}_conv, y = b{band_index}_bias)[name = string("b{band_index}_out")];""")
        outputs.append(f"b{band_index}_out")
        offset = end
    output_sig = ", ".join(outputs)
    body_text = "\n".join(body)
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {INPUT_DIM}, 1, {seq}]> x) {{
{body_text}
    }} -> ({output_sig});
}}
"""


def _band_split_weights(module) -> dict[str, bytes]:
    weights = {}
    for band_index, to_feature in enumerate(module.band_split.to_features):
        norm, linear = to_feature
        weights[f"@model_path/weights/b{band_index}_gamma.bin"] = _blob(norm.gamma.detach().cpu().numpy()[None, :, None, None])
        weights[f"@model_path/weights/b{band_index}_w.bin"] = _blob(linear.weight.detach().cpu().numpy()[:, :, None, None])
        weights[f"@model_path/weights/b{band_index}_bias.bin"] = _blob(linear.bias.detach().cpu().numpy()[None, :, None, None])
    return weights


def _band_split_weights_range(module, start: int, end: int) -> dict[str, bytes]:
    weights = {}
    for local_index, to_feature in enumerate(module.band_split.to_features[start:end]):
        norm, linear = to_feature
        weights[f"@model_path/weights/b{local_index}_gamma.bin"] = _blob(
            norm.gamma.detach().cpu().numpy()[None, :, None, None]
        )
        weights[f"@model_path/weights/b{local_index}_w.bin"] = _blob(
            linear.weight.detach().cpu().numpy()[:, :, None, None]
        )
        weights[f"@model_path/weights/b{local_index}_bias.bin"] = _blob(
            linear.bias.detach().cpu().numpy()[None, :, None, None]
        )
    return weights


def _band_feature_mil(dim_in: int, seq: int = TIME_SEQ) -> str:
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {dim_in}, 1, {seq}]> x) {{
{_conv_consts()}
{_rms_norm_mil_expr("norm", "x", 1, dim_in, seq, "@model_path/weights/gamma.bin")}
        tensor<fp16, [{DIM}, {dim_in}, 1, 1]> W = const()[name = string("W"), val = tensor<fp16, [{DIM}, {dim_in}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, 1]> B = const()[name = string("B"), val = tensor<fp16, [1, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, {seq}]> c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W, x = norm_out)[name = string("c")];
        tensor<fp16, [1, {DIM}, 1, {seq}]> out = add(x = c, y = B)[name = string("out")];
    }} -> (out);
}}
"""


def _band_feature_weights(to_feature) -> dict[str, bytes]:
    norm, linear = to_feature
    return {
        "@model_path/weights/gamma.bin": _blob(norm.gamma.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/w.bin": _blob(linear.weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/b.bin": _blob(linear.bias.detach().cpu().numpy()[None, :, None, None]),
    }


def _band_feature_tile_mil(dim_in: int, seq: int = TILE_SEQ) -> str:
    return _band_feature_mil(dim_in, seq)


def _band_feature_l2_tile_mil(dim_in: int, seq: int = TILE_SEQ) -> str:
    scale = dim_in ** 0.5
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {dim_in}, 1, {seq}]> x) {{
{_conv_consts()}
        tensor<fp16, [1, {dim_in}, 1, 1]> gamma = const()[name = string("gamma"), val = tensor<fp16, [1, {dim_in}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/gamma.bin"), offset = uint64(64)))];
        tensor<int32, [1]> rax = const()[name = string("rax"), val = tensor<int32, [1]>([1])];
        bool kd = const()[name = string("kd"), val = bool(true)];
        tensor<fp16, [1, 1, 1, {seq}]> l2 = reduce_l2_norm(x = x, axes = rax, keep_dims = kd)[name = string("l2")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> unit = real_div(x = x, y = l2)[name = string("unit")];
        fp16 scale = const()[name = string("scale"), val = fp16({scale})];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> scaled = mul(x = unit, y = scale)[name = string("scaled")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> norm_out = mul(x = scaled, y = gamma)[name = string("norm_out")];
        tensor<fp16, [{DIM}, {dim_in}, 1, 1]> W = const()[name = string("W"), val = tensor<fp16, [{DIM}, {dim_in}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, 1]> B = const()[name = string("B"), val = tensor<fp16, [1, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, {seq}]> c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W, x = norm_out)[name = string("c")];
        tensor<fp16, [1, {DIM}, 1, {seq}]> out = add(x = c, y = B)[name = string("out")];
    }} -> (out);
}}
"""


def _band_split_l2_tile_mil(dim_inputs: tuple[int, ...], seq: int = TILE_SEQ) -> str:
    body = [_conv_consts()]
    outputs = []
    offset = 0
    input_dim = sum(dim_inputs)
    for band_index, dim_in in enumerate(dim_inputs):
        begin = offset
        end = offset + dim_in
        scale = dim_in ** 0.5
        body.append(f"""
        tensor<int32, [4]> b{band_index}_begin = const()[name = string("b{band_index}_begin"), val = tensor<int32, [4]>([0, {begin}, 0, 0])];
        tensor<int32, [4]> b{band_index}_end = const()[name = string("b{band_index}_end"), val = tensor<int32, [4]>([1, {end}, 1, {seq}])];
        tensor<bool, [4]> b{band_index}_mask = const()[name = string("b{band_index}_mask"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> b{band_index}_stride = const()[name = string("b{band_index}_stride"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{band_index}_x = slice_by_index(begin = b{band_index}_begin, end = b{band_index}_end, end_mask = b{band_index}_mask, stride = b{band_index}_stride, x = x)[name = string("b{band_index}_x")];
        tensor<fp16, [1, {dim_in}, 1, 1]> b{band_index}_gamma = const()[name = string("b{band_index}_gamma"), val = tensor<fp16, [1, {dim_in}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{band_index}_gamma.bin"), offset = uint64(64)))];
        tensor<int32, [1]> b{band_index}_rax = const()[name = string("b{band_index}_rax"), val = tensor<int32, [1]>([1])];
        bool b{band_index}_kd = const()[name = string("b{band_index}_kd"), val = bool(true)];
        tensor<fp16, [1, 1, 1, {seq}]> b{band_index}_l2 = reduce_l2_norm(x = b{band_index}_x, axes = b{band_index}_rax, keep_dims = b{band_index}_kd)[name = string("b{band_index}_l2")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{band_index}_unit = real_div(x = b{band_index}_x, y = b{band_index}_l2)[name = string("b{band_index}_unit")];
        fp16 b{band_index}_scale = const()[name = string("b{band_index}_scale"), val = fp16({scale})];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{band_index}_scaled = mul(x = b{band_index}_unit, y = b{band_index}_scale)[name = string("b{band_index}_scaled")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{band_index}_norm_out = mul(x = b{band_index}_scaled, y = b{band_index}_gamma)[name = string("b{band_index}_norm_out")];
        tensor<fp16, [{DIM}, {dim_in}, 1, 1]> b{band_index}_w = const()[name = string("b{band_index}_w"), val = tensor<fp16, [{DIM}, {dim_in}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{band_index}_w.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, 1]> b{band_index}_bias = const()[name = string("b{band_index}_bias"), val = tensor<fp16, [1, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{band_index}_bias.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {DIM}, 1, {seq}]> b{band_index}_conv = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = b{band_index}_w, x = b{band_index}_norm_out)[name = string("b{band_index}_conv")];
        tensor<fp16, [1, {DIM}, 1, {seq}]> b{band_index}_out = add(x = b{band_index}_conv, y = b{band_index}_bias)[name = string("b{band_index}_out")];""")
        outputs.append(f"b{band_index}_out")
        offset = end
    output_sig = ", ".join(outputs)
    body_text = "\n".join(body)
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {input_dim}, 1, {seq}]> x) {{
{body_text}
    }} -> ({output_sig});
}}
"""


def _final_norm_mil(seq: int = TIME_SEQ, bands: int = FREQ_SEQ) -> str:
    batch = seq * bands
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {DIM}, 1, 1]> x) {{
{_rms_norm_mil_expr("norm", "x", batch, DIM, 1, "@model_path/weights/gamma.bin")}
    }} -> (norm_out);
}}
"""


def _final_norm_weights(module) -> dict[str, bytes]:
    return {"@model_path/weights/gamma.bin": _blob(module.final_norm.gamma.detach().cpu().numpy()[None, :, None, None])}


def _norm_tile_mil(batch: int, seq: int = TILE_SEQ) -> str:
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {DIM}, 1, {seq}]> x) {{
{_rms_norm_mil_expr("norm", "x", batch, DIM, seq, "@model_path/weights/gamma.bin")}
    }} -> (norm_out);
}}
"""


def _mask_band_mil(dim_in: int, seq: int = TILE_SEQ) -> str:
    out2 = dim_in * 2
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {DIM}, 1, {seq}]> x) {{
{_conv_consts()}
        tensor<fp16, [{MASK_HIDDEN}, {DIM}, 1, 1]> W1 = const()[name = string("W1"), val = tensor<fp16, [{MASK_HIDDEN}, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]> B1 = const()[name = string("B1"), val = tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> h1c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W1, x = x)[name = string("c1")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> h1 = add(x = h1c, y = B1)[name = string("b1")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]> twoh = const()[name = string("twoh"), val = tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/twoh.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]> oneh = const()[name = string("oneh"), val = tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/oneh.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> h2 = mul(x = h1, y = twoh)[name = string("h2")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> hs = sigmoid(x = h2)[name = string("hs")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> hs2 = mul(x = hs, y = twoh)[name = string("hs2")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> h = sub(x = hs2, y = oneh)[name = string("h")];
        tensor<fp16, [{out2}, {MASK_HIDDEN}, 1, 1]> W2 = const()[name = string("W2"), val = tensor<fp16, [{out2}, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {out2}, 1, 1]> B2 = const()[name = string("B2"), val = tensor<fp16, [1, {out2}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {out2}, 1, {seq}]> y0 = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W2, x = h)[name = string("c2")];
        tensor<fp16, [1, {out2}, 1, {seq}]> y = add(x = y0, y = B2)[name = string("b2")];
        tensor<int32, [4]> ba = const()[name = string("ba"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [4]> ea = const()[name = string("ea"), val = tensor<int32, [4]>([1, {dim_in}, 1, {seq}])];
        tensor<int32, [4]> bg = const()[name = string("bg"), val = tensor<int32, [4]>([0, {dim_in}, 0, 0])];
        tensor<int32, [4]> eg = const()[name = string("eg"), val = tensor<int32, [4]>([1, {out2}, 1, {seq}])];
        tensor<bool, [4]> em = const()[name = string("em"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> ss = const()[name = string("ss"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> a = slice_by_index(begin = ba, end = ea, end_mask = em, stride = ss, x = y)[name = string("a")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> g0 = slice_by_index(begin = bg, end = eg, end_mask = em, stride = ss, x = y)[name = string("g0")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> g = sigmoid(x = g0)[name = string("g")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> out = mul(x = a, y = g)[name = string("out")];
    }} -> (out);
}}
"""


def _mask_band_weights(estimator, band_index: int) -> dict[str, bytes]:
    layers = estimator._band_groupable_layers()[band_index]
    first_linear = layers[0][1]
    second_linear = layers[2][1]
    return {
        "@model_path/weights/w1.bin": _blob(first_linear.weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/b1.bin": _blob(first_linear.bias.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/w2.bin": _blob(second_linear.weight.detach().cpu().numpy()[:, :, None, None]),
        "@model_path/weights/b2.bin": _blob(second_linear.bias.detach().cpu().numpy()[None, :, None, None]),
        "@model_path/weights/twoh.bin": _blob(np.full((1, MASK_HIDDEN, 1, 1), 2, dtype=np.float16)),
        "@model_path/weights/oneh.bin": _blob(np.ones((1, MASK_HIDDEN, 1, 1), dtype=np.float16)),
    }


def _mask_band_weights_range(estimator, start: int, end: int) -> dict[str, bytes]:
    weights = {
        "@model_path/weights/twoh.bin": _blob(np.full((1, MASK_HIDDEN, 1, 1), 2, dtype=np.float16)),
        "@model_path/weights/oneh.bin": _blob(np.ones((1, MASK_HIDDEN, 1, 1), dtype=np.float16)),
    }
    band_layers = estimator._band_groupable_layers()
    for local_index, layers in enumerate(band_layers[start:end]):
        first_linear = layers[0][1]
        second_linear = layers[2][1]
        weights[f"@model_path/weights/b{local_index}_w1.bin"] = _blob(
            first_linear.weight.detach().cpu().numpy()[:, :, None, None]
        )
        weights[f"@model_path/weights/b{local_index}_b1.bin"] = _blob(
            first_linear.bias.detach().cpu().numpy()[None, :, None, None]
        )
        weights[f"@model_path/weights/b{local_index}_w2.bin"] = _blob(
            second_linear.weight.detach().cpu().numpy()[:, :, None, None]
        )
        weights[f"@model_path/weights/b{local_index}_b2.bin"] = _blob(
            second_linear.bias.detach().cpu().numpy()[None, :, None, None]
        )
    return weights


def _mask_group_mil(dim_in: int, group_count: int, seq: int = TILE_SEQ) -> str:
    input_dim = DIM * group_count
    out2 = dim_in * 2
    body = [_conv_consts(), f"""
        tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]> twoh = const()[name = string("twoh"), val = tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/twoh.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]> oneh = const()[name = string("oneh"), val = tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/oneh.bin"), offset = uint64(64)))];"""]
    outputs = []
    for local_index in range(group_count):
        begin = local_index * DIM
        end = begin + DIM
        body.append(f"""
        tensor<int32, [4]> b{local_index}_begin = const()[name = string("b{local_index}_begin"), val = tensor<int32, [4]>([0, {begin}, 0, 0])];
        tensor<int32, [4]> b{local_index}_end = const()[name = string("b{local_index}_end"), val = tensor<int32, [4]>([1, {end}, 1, {seq}])];
        tensor<bool, [4]> b{local_index}_mask = const()[name = string("b{local_index}_mask"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> b{local_index}_stride = const()[name = string("b{local_index}_stride"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [1, {DIM}, 1, {seq}]> b{local_index}_x = slice_by_index(begin = b{local_index}_begin, end = b{local_index}_end, end_mask = b{local_index}_mask, stride = b{local_index}_stride, x = x)[name = string("b{local_index}_x")];
        tensor<fp16, [{MASK_HIDDEN}, {DIM}, 1, 1]> b{local_index}_w1 = const()[name = string("b{local_index}_w1"), val = tensor<fp16, [{MASK_HIDDEN}, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{local_index}_w1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]> b{local_index}_b1 = const()[name = string("b{local_index}_b1"), val = tensor<fp16, [1, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{local_index}_b1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> b{local_index}_h1c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = b{local_index}_w1, x = b{local_index}_x)[name = string("b{local_index}_c1")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> b{local_index}_h1 = add(x = b{local_index}_h1c, y = b{local_index}_b1)[name = string("b{local_index}_add1")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> b{local_index}_h2 = mul(x = b{local_index}_h1, y = twoh)[name = string("b{local_index}_h2")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> b{local_index}_hs = sigmoid(x = b{local_index}_h2)[name = string("b{local_index}_hs")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> b{local_index}_hs2 = mul(x = b{local_index}_hs, y = twoh)[name = string("b{local_index}_hs2")];
        tensor<fp16, [1, {MASK_HIDDEN}, 1, {seq}]> b{local_index}_h = sub(x = b{local_index}_hs2, y = oneh)[name = string("b{local_index}_h")];
        tensor<fp16, [{out2}, {MASK_HIDDEN}, 1, 1]> b{local_index}_w2 = const()[name = string("b{local_index}_w2"), val = tensor<fp16, [{out2}, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{local_index}_w2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {out2}, 1, 1]> b{local_index}_b2 = const()[name = string("b{local_index}_b2"), val = tensor<fp16, [1, {out2}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b{local_index}_b2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {out2}, 1, {seq}]> b{local_index}_y0 = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = b{local_index}_w2, x = b{local_index}_h)[name = string("b{local_index}_c2")];
        tensor<fp16, [1, {out2}, 1, {seq}]> b{local_index}_y = add(x = b{local_index}_y0, y = b{local_index}_b2)[name = string("b{local_index}_add2")];
        tensor<int32, [4]> b{local_index}_ba = const()[name = string("b{local_index}_ba"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [4]> b{local_index}_ea = const()[name = string("b{local_index}_ea"), val = tensor<int32, [4]>([1, {dim_in}, 1, {seq}])];
        tensor<int32, [4]> b{local_index}_bg = const()[name = string("b{local_index}_bg"), val = tensor<int32, [4]>([0, {dim_in}, 0, 0])];
        tensor<int32, [4]> b{local_index}_eg = const()[name = string("b{local_index}_eg"), val = tensor<int32, [4]>([1, {out2}, 1, {seq}])];
        tensor<bool, [4]> b{local_index}_em = const()[name = string("b{local_index}_em"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> b{local_index}_ss = const()[name = string("b{local_index}_ss"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{local_index}_a = slice_by_index(begin = b{local_index}_ba, end = b{local_index}_ea, end_mask = b{local_index}_em, stride = b{local_index}_ss, x = b{local_index}_y)[name = string("b{local_index}_a")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{local_index}_g0 = slice_by_index(begin = b{local_index}_bg, end = b{local_index}_eg, end_mask = b{local_index}_em, stride = b{local_index}_ss, x = b{local_index}_y)[name = string("b{local_index}_g0")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{local_index}_g = sigmoid(x = b{local_index}_g0)[name = string("b{local_index}_g")];
        tensor<fp16, [1, {dim_in}, 1, {seq}]> b{local_index}_out = mul(x = b{local_index}_a, y = b{local_index}_g)[name = string("b{local_index}_out")];""")
        outputs.append(f"b{local_index}_out")
    body_text = "\n".join(body)
    output_sig = ", ".join(outputs)
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {input_dim}, 1, {seq}]> x) {{
{body_text}
    }} -> ({output_sig});
}}
"""


def _mask_group_concat_mil(dim_in: int, group_count: int, seq: int = TILE_SEQ) -> str:
    body = _mask_group_mil(dim_in, group_count, seq)
    marker = f"    }} -> ({', '.join(f'b{index}_out' for index in range(group_count))});"
    concat_inputs = ", ".join(f"b{index}_out" for index in range(group_count))
    replacement = f"""
        int32 concat_axis = const()[name = string("concat_axis"), val = int32(1)];
        bool concat_interleave = const()[name = string("concat_interleave"), val = bool(false)];
        tensor<fp16, [1, {dim_in * group_count}, 1, {seq}]> out = concat(values = ({concat_inputs}), axis = concat_axis, interleave = concat_interleave)[name = string("out")];
    }} -> (out);"""
    return body.replace(marker, replacement)


def _mask_grouped_conv_weights_range(estimator, start: int, end: int) -> dict[str, bytes]:
    group_count = end - start
    if group_count < 1:
        raise ValueError("private_ane grouped mask requires at least one band")
    band_layers = estimator._band_groupable_layers()
    first_linears = [band_layers[index][0][1] for index in range(start, end)]
    second_linears = [band_layers[index][2][1] for index in range(start, end)]
    dim_in = int(second_linears[0].out_features // 2)
    if any(int(layer.in_features) != DIM or int(layer.out_features) != MASK_HIDDEN for layer in first_linears):
        raise ValueError("private_ane grouped mask first linear shape mismatch")
    if any(int(layer.in_features) != MASK_HIDDEN or int(layer.out_features) != dim_in * 2 for layer in second_linears):
        raise ValueError("private_ane grouped mask second linear shape mismatch")

    w1 = np.concatenate(
        [layer.weight.detach().cpu().numpy()[:, :, None, None] for layer in first_linears],
        axis=0,
    )
    b1 = np.concatenate(
        [layer.bias.detach().cpu().numpy()[None, :, None, None] for layer in first_linears],
        axis=1,
    )
    w2 = np.concatenate(
        [layer.weight.detach().cpu().numpy()[:, :, None, None] for layer in second_linears],
        axis=0,
    )
    b2 = np.concatenate(
        [layer.bias.detach().cpu().numpy()[None, :, None, None] for layer in second_linears],
        axis=1,
    )
    return {
        "@model_path/weights/w1.bin": _blob(w1),
        "@model_path/weights/b1.bin": _blob(b1),
        "@model_path/weights/w2.bin": _blob(w2),
        "@model_path/weights/b2.bin": _blob(b2),
        "@model_path/weights/twoh.bin": _blob(np.full((1, group_count * MASK_HIDDEN, 1, 1), 2, dtype=np.float16)),
        "@model_path/weights/oneh.bin": _blob(np.ones((1, group_count * MASK_HIDDEN, 1, 1), dtype=np.float16)),
    }


def _mask_grouped_conv_mil(dim_in: int, group_count: int, seq: int = TILE_SEQ) -> str:
    input_dim = DIM * group_count
    hidden_dim = MASK_HIDDEN * group_count
    out2 = dim_in * 2
    out2_total = out2 * group_count
    out_total = dim_in * group_count
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [1, {input_dim}, 1, {seq}]> x) {{
        string pt = const()[name = string("pt"), val = string("valid")];
        tensor<int32, [2]> st = const()[name = string("st"), val = tensor<int32, [2]>([1, 1])];
        tensor<int32, [4]> pd = const()[name = string("pd"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [2]> dl = const()[name = string("dl"), val = tensor<int32, [2]>([1, 1])];
        int32 gr = const()[name = string("gr"), val = int32({group_count})];
        tensor<fp16, [{hidden_dim}, {DIM}, 1, 1]> W1 = const()[name = string("W1"), val = tensor<fp16, [{hidden_dim}, {DIM}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {hidden_dim}, 1, 1]> B1 = const()[name = string("B1"), val = tensor<fp16, [1, {hidden_dim}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b1.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {hidden_dim}, 1, {seq}]> h1c = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W1, x = x)[name = string("c1")];
        tensor<fp16, [1, {hidden_dim}, 1, {seq}]> h1 = add(x = h1c, y = B1)[name = string("b1")];
        tensor<fp16, [1, {hidden_dim}, 1, 1]> twoh = const()[name = string("twoh"), val = tensor<fp16, [1, {hidden_dim}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/twoh.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {hidden_dim}, 1, 1]> oneh = const()[name = string("oneh"), val = tensor<fp16, [1, {hidden_dim}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/oneh.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {hidden_dim}, 1, {seq}]> h2 = mul(x = h1, y = twoh)[name = string("h2")];
        tensor<fp16, [1, {hidden_dim}, 1, {seq}]> hs = sigmoid(x = h2)[name = string("hs")];
        tensor<fp16, [1, {hidden_dim}, 1, {seq}]> hs2 = mul(x = hs, y = twoh)[name = string("hs2")];
        tensor<fp16, [1, {hidden_dim}, 1, {seq}]> h = sub(x = hs2, y = oneh)[name = string("h")];
        tensor<fp16, [{out2_total}, {MASK_HIDDEN}, 1, 1]> W2 = const()[name = string("W2"), val = tensor<fp16, [{out2_total}, {MASK_HIDDEN}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {out2_total}, 1, 1]> B2 = const()[name = string("B2"), val = tensor<fp16, [1, {out2_total}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/b2.bin"), offset = uint64(64)))];
        tensor<fp16, [1, {out2_total}, 1, {seq}]> y0 = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W2, x = h)[name = string("c2")];
        tensor<fp16, [1, {out2_total}, 1, {seq}]> y = add(x = y0, y = B2)[name = string("b2")];
        tensor<int32, [4]> yshape = const()[name = string("yshape"), val = tensor<int32, [4]>([{group_count}, 2, {dim_in}, {seq}])];
        tensor<fp16, [{group_count}, 2, {dim_in}, {seq}]> yr = reshape(shape = yshape, x = y)[name = string("yr")];
        tensor<int32, [4]> ba = const()[name = string("ba"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [4]> ea = const()[name = string("ea"), val = tensor<int32, [4]>([{group_count}, 1, {dim_in}, {seq}])];
        tensor<int32, [4]> bg = const()[name = string("bg"), val = tensor<int32, [4]>([0, 1, 0, 0])];
        tensor<int32, [4]> eg = const()[name = string("eg"), val = tensor<int32, [4]>([{group_count}, 2, {dim_in}, {seq}])];
        tensor<bool, [4]> em = const()[name = string("em"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> ss = const()[name = string("ss"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [{group_count}, 1, {dim_in}, {seq}]> ar = slice_by_index(begin = ba, end = ea, end_mask = em, stride = ss, x = yr)[name = string("ar")];
        tensor<fp16, [{group_count}, 1, {dim_in}, {seq}]> g0r = slice_by_index(begin = bg, end = eg, end_mask = em, stride = ss, x = yr)[name = string("g0r")];
        tensor<int32, [4]> oshape = const()[name = string("oshape"), val = tensor<int32, [4]>([1, {out_total}, 1, {seq}])];
        tensor<fp16, [1, {out_total}, 1, {seq}]> a = reshape(shape = oshape, x = ar)[name = string("a")];
        tensor<fp16, [1, {out_total}, 1, {seq}]> g0 = reshape(shape = oshape, x = g0r)[name = string("g0")];
        tensor<fp16, [1, {out_total}, 1, {seq}]> g = sigmoid(x = g0)[name = string("g")];
        tensor<fp16, [1, {out_total}, 1, {seq}]> out = mul(x = a, y = g)[name = string("out")];
    }} -> (out);
}}
"""


def _stft_channel_seq_mil(frames: int, out_ch: int, n_fft: int = STFT_N_FFT, batch: int = 1) -> str:
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {n_fft}, 1, {frames}]> x) {{
{_conv_consts()}
        tensor<fp16, [{out_ch}, {n_fft}, 1, 1]> W = const()[name = string("W"), val = tensor<fp16, [{out_ch}, {n_fft}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w.bin"), offset = uint64(64)))];
        tensor<fp16, [{batch}, {out_ch}, 1, {frames}]> y = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W, x = x)[name = string("stft_linear")];
    }} -> (y);
}}
"""


def _stft_channel_seq_fused_mil(tile_channels: tuple[int, ...], frames: int, n_fft: int = STFT_N_FFT, batch: int = 1) -> str:
    body = [_conv_consts()]
    outputs = []
    total_out = sum(tile_channels)
    for tile_index, out_ch in enumerate(tile_channels):
        body.append(f"""
        tensor<fp16, [{out_ch}, {n_fft}, 1, 1]> W{tile_index} = const()[name = string("W{tile_index}"), val = tensor<fp16, [{out_ch}, {n_fft}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w{tile_index}.bin"), offset = uint64(64)))];
        tensor<fp16, [{batch}, {out_ch}, 1, {frames}]> y{tile_index} = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W{tile_index}, x = x)[name = string("stft_linear_{tile_index}")];""")
        outputs.append(f"y{tile_index}")
    body_text = "\n".join(body)
    output_sig = ", ".join(outputs)
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {n_fft}, 1, {frames}]> x) {{
{body_text}
        int32 cax = const()[name = string("cax"), val = int32(1)];
        bool cil = const()[name = string("cil"), val = bool(false)];
        tensor<fp16, [{batch}, {total_out}, 1, {frames}]> out = concat(axis = cax, interleave = cil, values = ({output_sig}))[name = string("stft_concat")];
    }} -> (out);
}}
"""


def _stft_dynamic_matmul_mil(
        frames: int,
        out_ch: int = STFT_OUT_TILE,
        n_fft: int = STFT_N_FFT,
        batch: int = 1,
) -> str:
    sp = frames + out_ch
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {n_fft}, 1, {sp}]> xh) {{
        tensor<int32, [4]> ba = const()[name = string("ba"), val = tensor<int32, [4]>([0, 0, 0, 0])];
        tensor<int32, [4]> sa = const()[name = string("sa"), val = tensor<int32, [4]>([{batch}, {n_fft}, 1, {frames}])];
        tensor<fp16, [{batch}, {n_fft}, 1, {frames}]> act = slice_by_size(x = xh, begin = ba, size = sa)[name = string("act")];
        tensor<int32, [4]> bw = const()[name = string("bw"), val = tensor<int32, [4]>([0, 0, 0, {frames}])];
        tensor<int32, [4]> sw = const()[name = string("sw"), val = tensor<int32, [4]>([{batch}, {n_fft}, 1, {out_ch}])];
        tensor<fp16, [{batch}, {n_fft}, 1, {out_ch}]> wt = slice_by_size(x = xh, begin = bw, size = sw)[name = string("wt")];
        tensor<int32, [4]> ra = const()[name = string("ra"), val = tensor<int32, [4]>([{batch}, 1, {n_fft}, {frames}])];
        tensor<fp16, [{batch}, 1, {n_fft}, {frames}]> a2 = reshape(shape = ra, x = act)[name = string("a2")];
        tensor<int32, [4]> pm = const()[name = string("pm"), val = tensor<int32, [4]>([0, 1, 3, 2])];
        tensor<fp16, [{batch}, 1, {frames}, {n_fft}]> a3 = transpose(perm = pm, x = a2)[name = string("a3")];
        tensor<int32, [4]> rw = const()[name = string("rw"), val = tensor<int32, [4]>([{batch}, 1, {n_fft}, {out_ch}])];
        tensor<fp16, [{batch}, 1, {n_fft}, {out_ch}]> W = reshape(shape = rw, x = wt)[name = string("W")];
        bool bF = const()[name = string("bF"), val = bool(false)];
        tensor<fp16, [{batch}, 1, {frames}, {out_ch}]> yh = matmul(transpose_x = bF, transpose_y = bF, x = a3, y = W)[name = string("mm")];
        tensor<fp16, [{batch}, 1, {out_ch}, {frames}]> yt = transpose(perm = pm, x = yh)[name = string("yt")];
        tensor<int32, [4]> ro = const()[name = string("ro"), val = tensor<int32, [4]>([{batch}, {out_ch}, 1, {frames}])];
        tensor<fp16, [{batch}, {out_ch}, 1, {frames}]> yr = reshape(shape = ro, x = yt)[name = string("yr")];
        tensor<fp16, [{batch}, {out_ch}, 1, {frames}]> y = identity(x = yr)[name = string("out")];
    }} -> (y);
}}
"""


def _ane_wakeup_spec(kind: str) -> tuple[str, str, dict[str, bytes], tuple[int, ...], int]:
    normalized = str(kind or "stft").lower()
    if normalized == "stft":
        input_shape = (1, STFT_N_FFT, 1, STFT_FRAME_TILE + STFT_FREQ_BINS * 2 - 2)
        output_bytes = (STFT_FREQ_BINS * 2 - 2) * STFT_FRAME_TILE * 2
        return (
            "stft",
            _stft_dynamic_matmul_mil(STFT_FRAME_TILE, STFT_FREQ_BINS * 2 - 2, STFT_N_FFT, 1),
            {},
            input_shape,
            output_bytes,
        )
    if normalized in ("matmul", "tiny_matmul"):
        n_fft = 64
        frames = 32
        out_ch = 32
        input_shape = (1, n_fft, 1, frames + out_ch)
        output_bytes = out_ch * frames * 2
        return (
            "matmul",
            _stft_dynamic_matmul_mil(frames, out_ch, n_fft, 1),
            {},
            input_shape,
            output_bytes,
        )
    raise ValueError("ANE wakeup kind must be 'stft' or 'matmul'")


def _stft_dft_weights(n_fft: int = STFT_N_FFT) -> np.ndarray:
    freq_bins = n_fft // 2 + 1
    n = np.arange(n_fft, dtype=np.float32)
    window = _periodic_hann_window_np(n_fft)
    weights = np.empty((freq_bins * 2, n_fft, 1, 1), dtype=np.float32)
    for k in range(freq_bins):
        phase = (2.0 * np.pi * float(k) / float(n_fft)) * n
        weights[2 * k, :, 0, 0] = window * np.cos(phase)
        weights[2 * k + 1, :, 0, 0] = -window * np.sin(phase)
    return weights


def _stft_dft_weight_tile(out_start: int, out_end: int, n_fft: int = STFT_N_FFT) -> np.ndarray:
    return _stft_dft_weight_rows(tuple(range(out_start, out_end)), n_fft)


@lru_cache(maxsize=8)
def _periodic_hann_window_np(n_fft: int = STFT_N_FFT) -> np.ndarray:
    n = np.arange(n_fft, dtype=np.float32)
    return (0.5 - 0.5 * np.cos((2.0 * np.pi / float(n_fft)) * n)).astype(np.float32, copy=False)


def _stft_dft_weight_rows(rows: tuple[int, ...], n_fft: int = STFT_N_FFT) -> np.ndarray:
    n = np.arange(n_fft, dtype=np.float32)
    window = _periodic_hann_window_np(n_fft)
    weights = np.empty((len(rows), n_fft, 1, 1), dtype=np.float32)
    for offset, row in enumerate(rows):
        k = row // 2
        phase = (2.0 * np.pi * float(k) / float(n_fft)) * n
        if row % 2 == 0:
            weights[offset, :, 0, 0] = window * np.cos(phase)
        else:
            weights[offset, :, 0, 0] = -window * np.sin(phase)
    return weights


@lru_cache(maxsize=1)
def _stft_dynamic_weight_tiles() -> tuple[tuple[int, int, np.ndarray], ...]:
    tiles = []
    for out_start, out_end in _stft_output_tile_ranges():
        weights = _stft_dft_weight_tile(out_start, out_end)
        if weights.shape[0] != STFT_OUT_TILE:
            padded = np.zeros((STFT_OUT_TILE, STFT_N_FFT, 1, 1), dtype=np.float32)
            padded[:weights.shape[0]] = weights
            weights = padded
        tiles.append((out_start, out_end, weights[:, :, 0, 0].T.copy()))
    return tuple(tiles)


@lru_cache(maxsize=1)
def _stft_dynamic_weight_groups() -> tuple[tuple[tuple[int, ...], np.ndarray], ...]:
    total_out_channels = STFT_FREQ_BINS * 2
    # The DC and Nyquist imaginary rows are identically zero for real-input
    # STFT. Skipping those two rows lets the dynamic ANE path fit all useful
    # DFT rows into one legal 2048-channel handle instead of a 2048 + padded
    # 128 split.
    compact_rows = (0, *range(2, total_out_channels - 1))
    n = np.arange(STFT_N_FFT, dtype=np.float32)
    window = _periodic_hann_window_np(STFT_N_FFT)
    step_real = np.cos((2.0 * np.pi / float(STFT_N_FFT)) * n).astype(np.float32)
    step_sin = np.sin((2.0 * np.pi / float(STFT_N_FFT)) * n).astype(np.float32)
    cur_real = np.ones(STFT_N_FFT, dtype=np.float32)
    cur_neg_sin = np.zeros(STFT_N_FFT, dtype=np.float32)
    weights = np.empty((len(compact_rows), STFT_N_FFT), dtype=np.float32)
    weights[0] = window
    offset = 1
    for _k in range(1, STFT_N_FFT // 2):
        next_real = cur_real * step_real + cur_neg_sin * step_sin
        next_neg_sin = cur_neg_sin * step_real - cur_real * step_sin
        cur_real, cur_neg_sin = next_real, next_neg_sin
        weights[offset] = window * cur_real
        offset += 1
        weights[offset] = window * cur_neg_sin
        offset += 1
    weights[offset] = window * (cur_real * step_real + cur_neg_sin * step_sin)
    return ((compact_rows, np.ascontiguousarray(weights.T, dtype=np.float16)),)


def _stft_dynamic_weight_groups_disk_cached(cache_tmpdir: str | os.PathLike | None):
    if not cache_tmpdir:
        return _stft_dynamic_weight_groups(), False, 0.0
    cache_dir = Path(cache_tmpdir) / "stft_weights"
    weight_path = cache_dir / f"dynamic_compact_n{STFT_N_FFT}_out{STFT_FREQ_BINS * 2 - 2}_fp16.npy"
    rows = (0, *range(2, STFT_FREQ_BINS * 2 - 1))
    started = time.perf_counter()
    try:
        if weight_path.exists():
            weights = np.load(weight_path, mmap_mode=None)
            if weights.shape == (STFT_N_FFT, len(rows)) and weights.dtype == np.float16:
                return ((rows, np.ascontiguousarray(weights)),), True, time.perf_counter() - started
    except (OSError, ValueError):
        pass
    groups = _stft_dynamic_weight_groups()
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(weight_path, groups[0][1], allow_pickle=False)
    except OSError:
        pass
    return groups, False, time.perf_counter() - started


def _split_stft_dynamic_weight_groups(
        groups: tuple[tuple[tuple[int, ...], np.ndarray], ...],
        max_outputs: int,
) -> tuple[tuple[tuple[int, ...], np.ndarray], ...]:
    if max_outputs <= 0:
        return groups
    split_groups = []
    for rows, weights in groups:
        if len(rows) <= max_outputs:
            split_groups.append((rows, weights))
            continue
        for start in range(0, len(rows), max_outputs):
            end = min(start + max_outputs, len(rows))
            split_groups.append((
                tuple(rows[start:end]),
                np.ascontiguousarray(weights[:, start:end], dtype=np.float16),
            ))
    return tuple(split_groups)


def warmup_private_ane_stft_weights() -> dict[str, object]:
    started = time.perf_counter()
    groups = _stft_dynamic_weight_groups()
    return {
        "wall_sec": float(time.perf_counter() - started),
        "groups": int(len(groups)),
        "out_ch": int(groups[0][1].shape[1]) if groups else 0,
        "n_fft": STFT_N_FFT,
        "dtype": str(groups[0][1].dtype) if groups else "",
    }


def _stft_output_tile_ranges(out_tile: int = STFT_OUT_TILE) -> tuple[tuple[int, int], ...]:
    total_out_channels = STFT_FREQ_BINS * 2
    return tuple((start, min(start + out_tile, total_out_channels)) for start in range(0, total_out_channels, out_tile))


def _group_stft_output_tiles(max_outputs: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    tiles = _stft_output_tile_ranges()
    return tuple(tuple(tiles[start:start + max_outputs]) for start in range(0, len(tiles), max_outputs))


def _irfft_channel_seq_mil(frames: int, out_ch: int, in_ch: int = STFT_FREQ_BINS * 2, batch: int = 1) -> str:
    return f"""program(1.3)
[buildInfo = dict<string, string>({{{{"coremlc-component-MIL", "3510.2.1"}}, {{"coremlc-version", "3505.4.1"}}, {{"coremltools-component-milinternal", ""}}, {{"coremltools-version", "9.0"}}}})]
{{
    func main<ios18>(tensor<fp16, [{batch}, {in_ch}, 1, {frames}]> x) {{
{_conv_consts()}
        tensor<fp16, [{out_ch}, {in_ch}, 1, 1]> W = const()[name = string("W"), val = tensor<fp16, [{out_ch}, {in_ch}, 1, 1]>(BLOBFILE(path = string("@model_path/weights/w.bin"), offset = uint64(64)))];
        tensor<fp16, [{batch}, {out_ch}, 1, {frames}]> y = conv(dilations = dl, groups = gr, pad = pd, pad_type = pt, strides = st, weight = W, x = x)[name = string("irfft_linear")];
    }} -> (y);
}}
"""


def _irfft_weights(n_fft: int = STFT_N_FFT) -> np.ndarray:
    freq_bins = n_fft // 2 + 1
    in_ch = freq_bins * 2
    n = np.arange(n_fft, dtype=np.float32)[:, None]
    k = np.arange(freq_bins, dtype=np.float32)[None, :]
    phase = (2.0 * np.pi / float(n_fft)) * n * k
    weights = np.zeros((n_fft, in_ch, 1, 1), dtype=np.float32)
    scale = 1.0 / float(n_fft)
    weights[:, 0::2, 0, 0] = 2.0 * scale * np.cos(phase)
    weights[:, 1::2, 0, 0] = -2.0 * scale * np.sin(phase)
    weights[:, 0, 0, 0] = scale
    weights[:, 1, 0, 0] = 0.0
    weights[:, 2 * (freq_bins - 1), 0, 0] = scale * np.cos(np.pi * np.arange(n_fft, dtype=np.float32))
    weights[:, 2 * (freq_bins - 1) + 1, 0, 0] = 0.0
    return weights


def _irfft_weight_tile(out_start: int, out_end: int, n_fft: int = STFT_N_FFT) -> np.ndarray:
    freq_bins = n_fft // 2 + 1
    in_ch = freq_bins * 2
    n = np.arange(out_start, out_end, dtype=np.float32)[:, None]
    k = np.arange(freq_bins, dtype=np.float32)[None, :]
    phase = (2.0 * np.pi / float(n_fft)) * n * k
    weights = np.zeros((out_end - out_start, in_ch, 1, 1), dtype=np.float32)
    scale = 1.0 / float(n_fft)
    weights[:, 0::2, 0, 0] = 2.0 * scale * np.cos(phase)
    weights[:, 1::2, 0, 0] = -2.0 * scale * np.sin(phase)
    weights[:, 0, 0, 0] = scale
    weights[:, 1, 0, 0] = 0.0
    weights[:, 2 * (freq_bins - 1), 0, 0] = scale * np.cos(np.pi * n[:, 0])
    weights[:, 2 * (freq_bins - 1) + 1, 0, 0] = 0.0
    return weights


def _attention_pre_tiled_mil(batch: int, seq: int, valid_seq: int, q_chunk: int) -> str:
    base = _attention_pre_mil(batch, seq, valid_seq)
    start_marker = '        bool tx = const()[name = string("tx")'
    end_marker = f"        tensor<fp16, [{batch}, {HEADS}, {HD}, {seq}]> at = transpose"
    start = base.index(start_marker)
    end = base.index(end_marker)
    scale = float(HD) ** -0.5
    chunks: list[str] = []
    names: list[str] = []
    use_mask = valid_seq < seq
    for index, q_start in enumerate(range(0, seq, q_chunk)):
        q_end = min(seq, q_start + q_chunk)
        q_len = q_end - q_start
        name = f"att_tile_{index}"
        names.append(name)
        mask_expr = f"masked{index}" if use_mask else f"scaled{index}"
        mask_block = ""
        if use_mask:
            mask_block = f"""
        tensor<fp16, [{batch}, {HEADS}, {q_len}, {seq}]> masked{index} = add(x = scaled{index}, y = score_mask)[name = string("masked_{index}")];"""
        chunks.append(f"""
        tensor<int32, [4]> q_b{index} = const()[name = string("q_b{index}"), val = tensor<int32, [4]>([0, 0, {q_start}, 0])];
        tensor<int32, [4]> q_e{index} = const()[name = string("q_e{index}"), val = tensor<int32, [4]>([{batch}, {HEADS}, {q_end}, {HD}])];
        tensor<bool, [4]> q_m{index} = const()[name = string("q_m{index}"), val = tensor<bool, [4]>([false, false, false, false])];
        tensor<int32, [4]> q_s{index} = const()[name = string("q_s{index}"), val = tensor<int32, [4]>([1, 1, 1, 1])];
        tensor<fp16, [{batch}, {HEADS}, {q_len}, {HD}]> qt{index} = slice_by_index(begin = q_b{index}, end = q_e{index}, end_mask = q_m{index}, stride = q_s{index}, x = q)[name = string("qt_{index}")];
        tensor<fp16, [{batch}, {HEADS}, {q_len}, {seq}]> scores{index} = matmul(transpose_x = tx, transpose_y = ty, x = qt{index}, y = k)[name = string("mm1_{index}")];
        tensor<fp16, [{batch}, {HEADS}, {q_len}, {seq}]> scaled{index} = mul(x = scores{index}, y = sc)[name = string("scale_{index}")];{mask_block}
        tensor<fp16, [{batch}, {HEADS}, {q_len}, {seq}]> aw{index} = softmax(axis = sax, x = {mask_expr})[name = string("sm_{index}")];
        tensor<fp16, [{batch}, {HEADS}, {q_len}, {HD}]> {name} = matmul(transpose_x = tx, transpose_y = tx, x = aw{index}, y = v)[name = string("mm2_{index}")];""")
    mask_const = ""
    if use_mask:
        mask_const = f"""
        tensor<fp16, [1, 1, 1, {seq}]> score_mask = const()[name = string("score_mask"), val = tensor<fp16, [1, 1, 1, {seq}]>(BLOBFILE(path = string("@model_path/weights/score_mask.bin"), offset = uint64(64)))];"""
    tiled_block = f"""
        bool tx = const()[name = string("tx"), val = bool(false)];
        bool ty = const()[name = string("ty"), val = bool(true)];
        fp16 sc = const()[name = string("sc"), val = fp16({scale})];
        int32 sax = const()[name = string("sax"), val = int32(-1)];
        int32 cax = const()[name = string("cax"), val = int32(2)];
        bool cil = const()[name = string("cil"), val = bool(false)];{mask_const}
{''.join(chunks)}
        tensor<fp16, [{batch}, {HEADS}, {seq}, {HD}]> att = concat(axis = cax, interleave = cil, values = ({", ".join(names)}))[name = string("att")];
"""
    return base[:start] + tiled_block + base[end:]


class PrivateANETransformerRunner:
    def __init__(self, module):
        self.module = module
        bridge_wrapper_route = getattr(module, "private_ane_bridge_wrapper_route", "default")
        if isinstance(bridge_wrapper_route, str):
            normalized = bridge_wrapper_route.strip().lower()
            if normalized in ("", "auto", "default", "none"):
                bridge_wrapper_route = "default"
            elif normalized in ("1", "true", "yes", "on"):
                bridge_wrapper_route = True
            elif normalized in ("0", "false", "no", "off"):
                bridge_wrapper_route = False
            else:
                raise ValueError(
                    "private_ane_bridge_wrapper_route must be one of "
                    "'default', 'true', 'false', '1', '0', 'yes', 'no', 'on', or 'off'"
                )
        if bridge_wrapper_route != "default":
            wrapper_env_keys = (
                "ANE_BRIDGE_CLIENT_FILE_LOAD",
                "ANE_BRIDGE_CLIENT_FILE_LOAD_ALL",
                "ANE_BRIDGE_CLIENT_FILE_PACK_WEIGHTS",
                "ANE_BRIDGE_CLIENT_FILE_WRAPPER",
            )
            if bool(bridge_wrapper_route):
                for key in wrapper_env_keys:
                    os.environ[key] = "1"
            else:
                for key in wrapper_env_keys:
                    os.environ.pop(key, None)
        bridge_client_variant = str(
            getattr(module, "private_ane_bridge_client_variant", "") or ""
        ).strip().lower()
        if bridge_client_variant in ("", "auto", "default", "none", "off"):
            os.environ.pop("ANE_BRIDGE_CLIENT_VARIANT", None)
        else:
            allowed_bridge_client_variants = {
                "shared",
                "private_shared",
                "restricted_yes",
                "restricted_no",
            }
            if bridge_client_variant not in allowed_bridge_client_variants:
                raise ValueError(
                    "private_ane_bridge_client_variant must be one of "
                    "'default', 'shared', 'private_shared', "
                    "'restricted_yes', or 'restricted_no'"
                )
            os.environ["ANE_BRIDGE_CLIENT_VARIANT"] = bridge_client_variant
        if bool(getattr(module, "private_ane_load_cache", False)):
            cache_tmpdir = getattr(module, "private_ane_cache_tmpdir", None)
            if cache_tmpdir:
                cache_path = Path(cache_tmpdir)
                cache_path.mkdir(parents=True, exist_ok=True)
                os.environ["TMPDIR"] = str(cache_path) + os.sep
                os.environ["ANE_BRIDGE_TMPDIR"] = str(cache_path)
            os.environ["ANE_BRIDGE_LOAD_CACHE"] = "1"
            # Bridge identifier directories are content-addressed by MIL+weights.
            # In this local experimental environment, size-match is sufficient to
            # skip re-reading every cached file on every load-cache hit. If a
            # stale cache directory ever slips through, load-only failure still
            # falls back to a fresh compile path.
            if "ANE_BRIDGE_SKIP_CONTENT_VERIFY" not in os.environ:
                os.environ["ANE_BRIDGE_SKIP_CONTENT_VERIFY"] = "1"
            if bool(getattr(module, "private_ane_keep_tmpdir", False)):
                os.environ["ANE_BRIDGE_KEEP_TMPDIR"] = "1"
            else:
                os.environ.pop("ANE_BRIDGE_KEEP_TMPDIR", None)
            if bool(getattr(module, "private_ane_skip_source_write_on_cache_hit", False)):
                os.environ["ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT"] = "1"
            else:
                os.environ.pop("ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT", None)
            # Runtime-clone cache is useful in focused bridge probes, but enabling
            # it globally for every private-ANE handle family keeps too many
            # anchor models alive and materially increases system memory
            # pressure. Keep it opt-in in the real pipeline until a narrower
            # reuse policy is implemented.
            if bool(getattr(module, "private_ane_runtime_clone_cache", False)):
                os.environ["ANE_BRIDGE_RUNTIME_CLONE_CACHE"] = "1"
            else:
                os.environ.pop("ANE_BRIDGE_RUNTIME_CLONE_CACHE", None)
        self.bridge = ANEBridge()
        self.last_timings = []
        self.last_stft_preload_timing = None
        self._block_cache = {}
        self._stft_handle_cache = {}
        self._stft_dynamic_weight_groups_cache = None
        self._dynamic_stft_input_initialized = set()
        self._irfft_handle_cache = {}
        self._band_split_handle_cache = {}
        self._final_norm_handle_cache = {}
        self._mask_handle_cache = {}
        self.last_memory_samples = []
        self.last_transformer_detail_timing = {}
        self._memory_probe_cache = (0.0, None, None, None, None)
        self._memory_sample_interval_sec = 0.10
        self._low_free_memory_strikes = 0
        self.memory_context = {}

    def _cache_enabled(self) -> bool:
        return bool(
            getattr(self.module, "private_ane_cache_transformers", False)
            and getattr(self.module, "private_ane_allow_transformer_handle_cache", False)
        )

    def _segment_cache_limit(self) -> int:
        if not bool(getattr(self.module, "private_ane_allow_transformer_handle_cache", False)):
            return 0
        return max(0, int(getattr(self.module, "private_ane_transformer_cache_segments", 0) or 0))

    def _max_transformer_layers(self) -> int:
        value = getattr(self.module, "private_ane_max_transformer_layers", None)
        if value in (None, "", 0, "0"):
            return len(self.module.layers)
        return min(len(self.module.layers), max(0, int(value)))

    def _skip_transformers(self) -> bool:
        value = getattr(self.module, "private_ane_skip_transformers", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _gelu_mode(self) -> str:
        mode = str(getattr(self.module, "private_ane_gelu_mode", "EXACT") or "EXACT").upper()
        if mode not in ("EXACT", "TANH_APPROXIMATION"):
            raise ValueError("private_ane_gelu_mode must be 'EXACT' or 'TANH_APPROXIMATION'")
        return mode

    def _fuse_residual(self) -> bool:
        value = getattr(self.module, "private_ane_fuse_residual", True)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _fuse_gate_ffn(self) -> bool:
        value = getattr(self.module, "private_ane_fuse_gate_ffn", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _fuse_gate_ffn_axis(self, axis: str, batch: int | None = None, seq: int | None = None) -> bool:
        if not self._fuse_gate_ffn():
            return False
        if batch is None or seq is None:
            return axis == "freq"
        if axis == "freq":
            return True
        max_work_items = int(getattr(self.module, "private_ane_fuse_gate_ffn_max_work_items", 8192) or 0)
        if max_work_items > 0 and int(batch) * int(seq) > max_work_items:
            return False
        return True

    def _two_input_gate(self) -> bool:
        value = getattr(self.module, "private_ane_two_input_gate", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _bridge_pack_gate(self) -> bool:
        value = getattr(self.module, "private_ane_bridge_pack_gate", True)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _surface_handoff_gate_ffn(self) -> bool:
        value = getattr(self.module, "private_ane_surface_handoff_gate_ffn", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _batch_axis_eval(self) -> bool:
        value = getattr(self.module, "private_ane_batch_axis_eval", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    @staticmethod
    def _batch_axis_attention_pre_supported(axis: str, batch: int, seq: int) -> bool:
        # Evidence from benchmark/private_ane_batch_acceptance_probe.py and
        # two-chunk smoke runs: freq attention/full-block compile-load and eval
        # work through 4 chunks (batch=3752, seq=64). Time batch=124/seq=960
        # can compile/load, but eval creates multi-GiB wired pressure and is
        # killed by the native supervisor, so time stays per-chunk for now.
        if axis == "time":
            return seq == TIME_PAD and batch <= FREQ_SEQ
        if axis == "freq":
            return seq == FREQ_PAD and batch <= 4 * TIME_SEQ
        return False

    def _tiled_time_attention_pre(self) -> bool:
        value = getattr(self.module, "private_ane_tiled_time_attention_pre", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _tiled_attention_pre_axis(self, axis: str, layer_index: int | None = None) -> bool:
        if axis != "time" or not self._tiled_time_attention_pre():
            return False
        force_all_layers = os.environ.get(
            "PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS",
            "",
        ).lower() in ("1", "true", "yes", "on")
        if force_all_layers:
            return True
        # Keep layer 1+ disabled by default: the forced diagnostic seam compiles,
        # but adds more materialization cost than eval savings.
        return layer_index in (None, 0)

    def _tiled_attention_pre_for_shape(
            self,
            axis: str,
            layer_index: int | None,
            batch: int,
            seq: int,
            valid_seq: int,
    ) -> bool:
        if not self._tiled_attention_pre_axis(axis, layer_index):
            return False
        force_small_shapes = os.environ.get(
            "PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_SMALL_SHAPES",
            "",
        ).lower() in ("1", "true", "yes", "on")
        if force_small_shapes:
            return True
        # 2026-06-24 evidence:
        # batch=4 q240 is slower, batch=62 q240 is faster for time attention_pre.
        # Keep q240 large-shape-only until intermediate batch sizes are measured.
        return axis == "time" and seq == TIME_PAD and valid_seq <= seq and batch >= FREQ_SEQ

    def _tiled_time_attention_pre_q_chunk(self) -> int:
        q_chunk = int(getattr(self.module, "private_ane_tiled_time_attention_pre_q_chunk", 128) or 128)
        if q_chunk < 1:
            raise ValueError("private_ane_tiled_time_attention_pre_q_chunk must be >= 1")
        return q_chunk

    def _direct_time_to_freq_repack(self) -> bool:
        return bool(getattr(self.module, "private_ane_direct_time_to_freq_repack", False))

    def _direct_time_to_freq_unpadded(self) -> bool:
        return bool(getattr(self.module, "private_ane_direct_time_to_freq_unpadded", False))

    def _transformer_hot_gc_interval(self) -> int:
        value = getattr(
            self.module,
            "private_ane_transformer_hot_gc_interval",
            DEFAULT_PRIVATE_ANE_TRANSFORMER_HOT_GC_INTERVAL,
        )
        if value in (None, ""):
            value = DEFAULT_PRIVATE_ANE_TRANSFORMER_HOT_GC_INTERVAL
        interval = int(value)
        if interval < 0:
            raise ValueError("private_ane_transformer_hot_gc_interval must be >= 0")
        return interval

    def _transformer_guard_interval(self) -> int:
        value = getattr(
            self.module,
            "private_ane_transformer_guard_interval",
            DEFAULT_PRIVATE_ANE_TRANSFORMER_GUARD_INTERVAL,
        )
        if value in (None, ""):
            value = DEFAULT_PRIVATE_ANE_TRANSFORMER_GUARD_INTERVAL
        interval = int(value)
        if interval < 0:
            raise ValueError("private_ane_transformer_guard_interval must be >= 0")
        return interval

    @staticmethod
    def _interval_enabled(interval: int, segment_index: int) -> bool:
        return interval > 0 and (int(segment_index) + 1) % interval == 0

    def _profile_hot_transformer_gc(self, segment_index: int) -> tuple[float, bool]:
        if not self._interval_enabled(self._transformer_hot_gc_interval(), segment_index):
            return 0.0, False
        started = time.perf_counter()
        gc.collect()
        return time.perf_counter() - started, True

    def _profile_transformer_guard(self, label: str, segment_index: int, *, force: bool = False) -> tuple[float, bool]:
        if not force and not self._interval_enabled(self._transformer_guard_interval(), segment_index):
            return 0.0, False
        started = time.perf_counter()
        self._guard_memory(label, segment_index)
        return time.perf_counter() - started, True

    def _attention_pre_mil_for_axis(
            self,
            axis: str,
            layer_index: int,
            batch: int,
            seq: int,
            valid_seq: int,
    ) -> str | None:
        if not self._tiled_attention_pre_for_shape(axis, layer_index, batch, seq, valid_seq):
            return None
        return _attention_pre_tiled_mil(
            batch,
            seq,
            valid_seq,
            min(seq, self._tiled_time_attention_pre_q_chunk()),
        )

    def _persistent_aux_handles(self) -> bool:
        value = getattr(self.module, "private_ane_persistent_aux_handles", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _persistent_stft_handles(self) -> bool:
        value = getattr(self.module, "private_ane_persistent_stft_handles", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _dynamic_stft(self) -> bool:
        value = getattr(self.module, "private_ane_dynamic_stft", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _dynamic_stft_max_outputs(self) -> int:
        value = int(getattr(self.module, "private_ane_dynamic_stft_max_outputs", STFT_FREQ_BINS * 2 - 2) or 0)
        if value <= 0:
            return STFT_FREQ_BINS * 2 - 2
        return max(1, min(value, STFT_FREQ_BINS * 2 - 2))

    def _native_dynamic_stft_input_weights(self) -> bool:
        value = getattr(self.module, "private_ane_native_dynamic_stft_input_weights", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _dynamic_stft_weight_groups(self):
        if self._stft_dynamic_weight_groups_cache is not None:
            return self._stft_dynamic_weight_groups_cache, True, 0.0
        rows = (0, *range(2, STFT_FREQ_BINS * 2 - 1))
        max_outputs = self._dynamic_stft_max_outputs()
        if self._native_dynamic_stft_input_weights() and max_outputs >= len(rows):
            groups = ((rows, None),)
            self._stft_dynamic_weight_groups_cache = groups
            return groups, False, 0.0
        if bool(getattr(self.module, "private_ane_stft_weight_disk_cache", False)):
            groups, cache_hit, cache_sec = _stft_dynamic_weight_groups_disk_cached(
                getattr(self.module, "private_ane_cache_tmpdir", None)
            )
        else:
            started = time.perf_counter()
            try:
                weights, native_sec = self.bridge.build_stft_dynamic_weights_fp16(STFT_N_FFT, len(rows))
                groups = ((rows, weights),)
                cache_sec = native_sec
            except (AttributeError, RuntimeError):
                groups = _stft_dynamic_weight_groups()
                cache_sec = time.perf_counter() - started
            cache_hit = False
        groups = _split_stft_dynamic_weight_groups(groups, max_outputs)
        self._stft_dynamic_weight_groups_cache = groups
        return groups, cache_hit, cache_sec

    def _fused_stft(self) -> bool:
        value = getattr(self.module, "private_ane_fused_stft", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _fused_stft_max_outputs(self) -> int:
        value = int(getattr(self.module, "private_ane_fused_stft_max_outputs", 17) or 17)
        if value < 1:
            raise ValueError("private_ane_fused_stft_max_outputs must be >= 1")
        return value

    def _stft_frame_tile(self) -> int:
        value = int(getattr(self.module, "private_ane_stft_frame_tile", STFT_FRAME_TILE) or STFT_FRAME_TILE)
        if value < 1:
            raise ValueError("private_ane_stft_frame_tile must be >= 1")
        return min(value, TIME_SEQ)

    def _preload_stft_handles(self) -> bool:
        value = getattr(self.module, "private_ane_preload_stft_handles", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def preserve_aux_handles_between_batches(self) -> bool:
        return self._persistent_aux_handles()

    def preserve_stft_handles_between_batches(self) -> bool:
        return self._persistent_stft_handles() or self._preload_stft_handles()

    def maybe_preload_stft_handles(self) -> dict[str, object] | None:
        if not self._preload_stft_handles() or self._stft_handle_cache:
            return None
        return self.preload_stft_handles()

    def _fused_band_split_max_outputs(self) -> int:
        value = getattr(self.module, "private_ane_fused_band_split_max_outputs", FUSED_BAND_SPLIT_MAX_OUTPUTS)
        max_outputs = int(value)
        if max_outputs < 1:
            raise ValueError("private_ane_fused_band_split_max_outputs must be >= 1")
        return max_outputs

    def _fused_mask_max_outputs(self) -> int:
        value = getattr(self.module, "private_ane_fused_mask_estimator_max_outputs", FUSED_MASK_MAX_OUTPUTS)
        max_outputs = int(value)
        if max_outputs < 1:
            raise ValueError("private_ane_fused_mask_estimator_max_outputs must be >= 1")
        return max_outputs

    def _batch_stft_istft_channels(self) -> bool:
        value = getattr(self.module, "private_ane_stft_istft_batch_channels", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _stft_bridge_qos(self) -> int | None:
        value = getattr(self.module, "private_ane_stft_bridge_qos", "auto")
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("", "auto"):
                return None if os.environ.get("ANE_BRIDGE_QOS") else DEFAULT_PRIVATE_ANE_STFT_BRIDGE_QOS
            if normalized in ("default", "global", "none", "off"):
                return None
            value = normalized
        if value is None:
            return None
        qos = int(value)
        if qos < 0 or qos > 63:
            raise ValueError("private_ane_stft_bridge_qos must be in [0, 63], 'auto', or 'global'")
        return qos

    def _stft_bridge_qos_scope(self):
        return self._stft_bridge_env_scope()

    def _stft_bridge_atomic_writes(self) -> str | None:
        value = getattr(self.module, "private_ane_stft_atomic_writes", "auto")
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("", "auto"):
                return None if os.environ.get("ANE_BRIDGE_ATOMIC_WRITES") else "0"
            if normalized in ("default", "global", "none"):
                return None
            if normalized in ("0", "false", "no", "off", "nonatomic", "non-atomic"):
                return "0"
            if normalized in ("1", "true", "yes", "on", "atomic"):
                return "1"
            raise ValueError(
                "private_ane_stft_atomic_writes must be 'auto', 'global', "
                "'atomic', 'non-atomic', or a boolean"
            )
        return "1" if bool(value) else "0"

    def _stft_bridge_tmpdir(self) -> str | None:
        value = os.environ.get("ANE_BRIDGE_STFT_TMPDIR") or getattr(
            self.module,
            "private_ane_stft_cache_tmpdir",
            "auto",
        )
        if isinstance(value, str):
            normalized = value.strip()
            lowered = normalized.lower()
            if lowered in ("", "auto"):
                return None
            elif lowered in ("default", "global", "none", "off"):
                return None
            else:
                path = normalized
        elif value is None:
            return None
        elif isinstance(value, bool):
            if not value:
                return None
            path = DEFAULT_PRIVATE_ANE_STFT_CACHE_TMPDIR
        else:
            path = os.fspath(value)
        cache_path = Path(path)
        cache_path.mkdir(parents=True, exist_ok=True)
        return str(cache_path)

    def _stft_bridge_keep_tmpdir(self) -> str | None:
        value = os.environ.get("ANE_BRIDGE_STFT_KEEP_TMPDIR") or getattr(
            self.module,
            "private_ane_stft_keep_tmpdir",
            True,
        )
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("", "auto", "default", "global"):
                return "1"
            if normalized in ("1", "true", "yes", "on"):
                return "1"
            if normalized in ("0", "false", "no", "off"):
                return "0"
            raise ValueError("private_ane_stft_keep_tmpdir must be a boolean or one of auto/global/off/on")
        return "1" if bool(value) else "0"

    @contextmanager
    def _stft_bridge_env_scope(self):
        with _temporary_env_value("ANE_BRIDGE_QOS", self._stft_bridge_qos()):
            with _temporary_env_value("ANE_BRIDGE_ATOMIC_WRITES", self._stft_bridge_atomic_writes()):
                # STFT static handles are compile-sensitive to inherited global
                # ANE_BRIDGE_TMPDIR values. When STFT does not request its own
                # tmpdir, explicitly clear the global bridge tmpdir inside the
                # STFT scope instead of inheriting the non-STFT cache path.
                with _temporary_env_value(
                        "ANE_BRIDGE_TMPDIR",
                        self._stft_bridge_tmpdir(),
                        clear_if_none=True,
                ):
                    with _temporary_env_value("ANE_BRIDGE_KEEP_TMPDIR", self._stft_bridge_keep_tmpdir()):
                        yield

    def _stft_bridge_qos_label(self) -> str:
        qos = self._stft_bridge_qos()
        if qos is not None:
            return str(qos)
        return os.environ.get("ANE_BRIDGE_QOS") or "bridge_default"

    def _stft_bridge_atomic_writes_label(self) -> str:
        value = self._stft_bridge_atomic_writes()
        if value is not None:
            return value
        return os.environ.get("ANE_BRIDGE_ATOMIC_WRITES") or "bridge_default"

    def _stft_bridge_eval(self, handle) -> None:
        with self._stft_bridge_qos_scope():
            self.bridge.eval(handle)

    def _stft_bridge_run(self, handle, x: np.ndarray, out_shape: tuple[int, ...]) -> np.ndarray:
        with self._stft_bridge_qos_scope():
            return self.bridge.run(handle, x, out_shape)

    def _memory_limits(self):
        max_rss_mb = _optional_float(
            getattr(self.module, "private_ane_max_rss_mb", DEFAULT_PRIVATE_ANE_MAX_RSS_MB),
            DEFAULT_PRIVATE_ANE_MAX_RSS_MB,
        )
        min_free_memory_percent = _optional_int(
            getattr(self.module, "private_ane_min_free_memory_percent", DEFAULT_PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT),
            DEFAULT_PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT,
        )
        if (
                min_free_memory_percent is not None
                and min_free_memory_percent < MIN_PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT
        ):
            raise ValueError(
                "private_ane_min_free_memory_percent must be >= "
                f"{MIN_PRIVATE_ANE_MIN_FREE_MEMORY_PERCENT}, or 0 to disable the soft guard"
            )
        emergency_free_memory_percent = _optional_int(
            getattr(
                self.module,
                "private_ane_emergency_free_memory_percent",
                DEFAULT_PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT,
            ),
            DEFAULT_PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT,
        )
        if (
                emergency_free_memory_percent is not None
                and emergency_free_memory_percent < MIN_PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT
        ):
            raise ValueError(
                "private_ane_emergency_free_memory_percent must be >= "
                f"{MIN_PRIVATE_ANE_EMERGENCY_FREE_MEMORY_PERCENT}, or 0 to disable"
            )
        max_ane_service_rss_mb = _optional_float(
            getattr(self.module, "private_ane_max_ane_service_rss_mb", DEFAULT_PRIVATE_ANE_MAX_ANE_SERVICE_RSS_MB),
            DEFAULT_PRIVATE_ANE_MAX_ANE_SERVICE_RSS_MB,
        )
        max_swap_used_mb = _optional_float(
            getattr(self.module, "private_ane_max_swap_used_mb", DEFAULT_PRIVATE_ANE_MAX_SWAP_USED_MB),
            DEFAULT_PRIVATE_ANE_MAX_SWAP_USED_MB,
        )
        if (
                max_swap_used_mb is not None
                and (max_swap_used_mb < 0 or max_swap_used_mb > MAX_PRIVATE_ANE_MAX_SWAP_USED_MB)
        ):
            raise ValueError(
                "private_ane_max_swap_used_mb must be <= "
                f"{MAX_PRIVATE_ANE_MAX_SWAP_USED_MB}, or 0 to disable"
            )
        return (
            max_rss_mb,
            min_free_memory_percent,
            emergency_free_memory_percent,
            max_ane_service_rss_mb,
            max_swap_used_mb,
        )

    def _free_memory_strikes_limit(self) -> int:
        value = getattr(self.module, "private_ane_free_memory_strikes", DEFAULT_PRIVATE_ANE_FREE_MEMORY_STRIKES)
        if value in (None, "", 0, "0"):
            return DEFAULT_PRIVATE_ANE_FREE_MEMORY_STRIKES
        return max(1, int(value))

    def _memory_values(self):
        now = time.perf_counter()
        cached_at, rss_mb, free_percent, ane_service_rss_mb, swap_used_mb = self._memory_probe_cache
        if cached_at > 0.0 and now - cached_at < self._memory_sample_interval_sec:
            return rss_mb, free_percent, ane_service_rss_mb, swap_used_mb, False
        rss_mb = _current_rss_mb()
        free_percent = _system_free_memory_percent()
        ane_service_rss_mb = _ane_service_rss_mb()
        swap_used_mb = _system_swap_used_mb()
        self._memory_probe_cache = (now, rss_mb, free_percent, ane_service_rss_mb, swap_used_mb)
        return rss_mb, free_percent, ane_service_rss_mb, swap_used_mb, True

    def _guard_memory(self, label: str, segment_index: int | None = None) -> None:
        (
            max_rss_mb,
            min_free_memory_percent,
            emergency_free_memory_percent,
            max_ane_service_rss_mb,
            max_swap_used_mb,
        ) = self._memory_limits()
        sample = {"label": label}
        if segment_index is not None:
            sample["segment"] = int(segment_index)
        context = getattr(self, "memory_context", None)
        if isinstance(context, dict):
            for key, value in context.items():
                if value is not None:
                    sample[key] = value
        rss_mb, free_percent, ane_service_rss_mb, swap_used_mb, fresh_sample = self._memory_values()
        if rss_mb is not None:
            sample["rss_mb"] = float(rss_mb)
        if free_percent is not None:
            sample["free_memory_percent"] = int(free_percent)
        if ane_service_rss_mb is not None:
            sample["ane_service_rss_mb"] = float(ane_service_rss_mb)
        if swap_used_mb is not None:
            sample["swap_used_mb"] = float(swap_used_mb)
        sample["cache_handles"] = self.cache_handle_counts()
        self.last_memory_samples.append(sample)
        if len(self.last_memory_samples) > MAX_MEMORY_SAMPLES:
            del self.last_memory_samples[:len(self.last_memory_samples) - MAX_MEMORY_SAMPLES]
        context_suffix = ""
        if isinstance(context, dict) and context:
            context_suffix = " context=" + repr({
                key: value for key, value in context.items() if value is not None
            })
        if max_rss_mb is not None and rss_mb is not None and rss_mb > max_rss_mb:
            raise MemoryError(
                f"private_ane RSS exceeded limit: {rss_mb:.1f} MB > {max_rss_mb:.1f} MB "
                f"at {label}{context_suffix}"
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
                f"{ane_service_rss_mb:.1f} MB > {max_ane_service_rss_mb:.1f} MB at {label}"
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
            if fresh_sample:
                self._low_free_memory_strikes += 1
            strike_limit = self._free_memory_strikes_limit()
            if self._low_free_memory_strikes >= strike_limit:
                raise MemoryError(
                    "private_ane stopped because system free memory is low: "
                    f"{free_percent}% < {min_free_memory_percent}% at {label} "
                    f"for {self._low_free_memory_strikes} consecutive samples"
                )
        else:
            self._low_free_memory_strikes = 0

    @staticmethod
    def _validate_shape(x: np.ndarray) -> None:
        if x.shape != (1, TIME_SEQ, FREQ_SEQ, DIM):
            raise ValueError(f"private_ane expects transformer input shape (1,{TIME_SEQ},{FREQ_SEQ},{DIM}), got {x.shape}")

    def _compile_run_free_axis(self, axis: str, layer_index: int, x_ane: np.ndarray, seq: int, valid_seq: int):
        gelu_mode = self._gelu_mode()
        fuse_residual = self._fuse_residual()
        fuse_gate_ffn = self._fuse_gate_ffn_axis(axis, x_ane.shape[0], seq)
        two_input_gate = self._two_input_gate()
        tiled_attention_pre = self._tiled_attention_pre_for_shape(
            axis,
            layer_index,
            x_ane.shape[0],
            seq,
            valid_seq,
        )
        tiled_q_chunk = self._tiled_time_attention_pre_q_chunk() if tiled_attention_pre else 0
        cache_key = (
            axis,
            layer_index,
            seq,
            valid_seq,
            x_ane.shape[0],
            gelu_mode,
            fuse_residual,
            fuse_gate_ffn,
            two_input_gate,
            self._surface_handoff_gate_ffn(),
            tiled_attention_pre,
            tiled_q_chunk,
        )
        if self._cache_enabled() and cache_key in self._block_cache:
            handles = self._block_cache[cache_key]
            self._guard_memory(f"{axis}_layer{layer_index}_cache_hit")
            eval_started = time.perf_counter()
            out, _ = self._run_block_profiled(handles, x_ane, fuse_gate_ffn)
            eval_sec = time.perf_counter() - eval_started
            self._guard_memory(f"{axis}_layer{layer_index}_after_eval")
            return out, (0.0, 0.0, 0.0), eval_sec

        handles = None
        attn, ffn = _block_modules(self.module, axis, layer_index)
        def memory_guard(stage: str) -> None:
            self._guard_memory(f"{axis}_layer{layer_index}_{stage}")

        try:
            if fuse_gate_ffn:
                handles, compile_times, _compile_profiles = _compile_fused_gate_ffn_block(
                    self.bridge,
                    attn,
                    ffn,
                    x_ane.shape[0],
                    seq,
                    valid_seq,
                    gelu_mode,
                    x_ane.nbytes,
                    memory_guard=memory_guard,
                    attention_pre_mil=self._attention_pre_mil_for_axis(axis, layer_index, x_ane.shape[0], seq, valid_seq),
                )
            else:
                handles, compile_times, _compile_profiles = _compile_block(
                    self.bridge,
                    attn,
                    ffn,
                    x_ane.shape[0],
                    seq,
                    valid_seq,
                    gelu_mode,
                    x_ane.nbytes,
                    memory_guard=memory_guard,
                    fuse_residual=fuse_residual,
                    two_input_gate=two_input_gate,
                    attention_pre_mil=self._attention_pre_mil_for_axis(axis, layer_index, x_ane.shape[0], seq, valid_seq),
                )
            eval_started = time.perf_counter()
            out, _ = self._run_block_profiled(handles, x_ane, fuse_gate_ffn)
            eval_sec = time.perf_counter() - eval_started
            self._guard_memory(f"{axis}_layer{layer_index}_after_eval")
            if self._cache_enabled():
                self._block_cache[cache_key] = handles
                handles = None
            return out, compile_times, eval_sec
        finally:
            if handles is not None:
                for handle in handles:
                    self.bridge.free(handle)
            gc.collect()

    def cache_handle_counts(self) -> dict[str, int]:
        transformer_handles = 0
        for handles in self._block_cache.values():
            try:
                transformer_handles += len(handles)
            except TypeError:
                transformer_handles += 1
        stft_handles = len(self._stft_handle_cache)
        irfft_handles = len(self._irfft_handle_cache)
        band_split_handles = len(self._band_split_handle_cache)
        final_norm_handles = len(self._final_norm_handle_cache)
        mask_handles = len(self._mask_handle_cache)
        aux_handles = band_split_handles + final_norm_handles + mask_handles
        non_transformer_handles = stft_handles + irfft_handles + aux_handles
        return {
            "transformer_entries": len(self._block_cache),
            "transformer_handles": transformer_handles,
            "stft_handles": stft_handles,
            "irfft_handles": irfft_handles,
            "band_split_handles": band_split_handles,
            "final_norm_handles": final_norm_handles,
            "mask_handles": mask_handles,
            "aux_handles": aux_handles,
            "non_transformer_handles": non_transformer_handles,
            "total_handles": transformer_handles + non_transformer_handles,
        }

    @staticmethod
    def _cache_release_summary(before: dict[str, int], after: dict[str, int]) -> dict[str, object]:
        released = {}
        for key, before_value in before.items():
            after_value = after.get(key, 0)
            released[key] = max(0, int(before_value) - int(after_value))
        return {
            "before": before,
            "after": after,
            "released": released,
            "released_total_handles": int(released.get("total_handles", 0)),
        }

    def clear_transformer_cache(self) -> dict[str, object]:
        before = self.cache_handle_counts()
        if before.get("transformer_handles", 0) <= 0:
            return self._cache_release_summary(before, before)
        total_free = 0.0
        handle_count = 0
        for handles in self._block_cache.values():
            for handle in handles:
                started = time.perf_counter()
                self.bridge.free(handle, label="transformer_cache")
                total_free += time.perf_counter() - started
                handle_count += 1
        self._block_cache.clear()
        gc_started = time.perf_counter()
        gc.collect()
        gc_sec = time.perf_counter() - gc_started
        self._record_free_profile("transformer_cache", total_free, gc_sec, handle_count)
        return self._cache_release_summary(before, self.cache_handle_counts())

    def clear_non_transformer_cache(
            self,
            *,
            preserve_aux_handles: bool = False,
            preserve_stft_handles: bool = False,
    ) -> dict[str, object]:
        before = self.cache_handle_counts()
        release_any = False
        if not preserve_stft_handles and before.get("stft_handles", 0) > 0:
            self.clear_stft_cache()
            release_any = True
        if before.get("irfft_handles", 0) > 0:
            self.clear_irfft_cache()
            release_any = True
        if not preserve_aux_handles and before.get("aux_handles", 0) > 0:
            self.clear_aux_handle_cache()
            release_any = True
        if release_any:
            gc.collect()
        return self._cache_release_summary(before, self.cache_handle_counts())

    def clear_cache(
            self,
            *,
            preserve_aux_handles: bool = False,
            preserve_stft_handles: bool = False,
    ) -> dict[str, object]:
        before = self.cache_handle_counts()
        release_transformer = before.get("transformer_handles", 0) > 0
        release_non_transformer = (
            before.get("irfft_handles", 0) > 0
            or (before.get("stft_handles", 0) > 0 and not preserve_stft_handles)
            or (before.get("aux_handles", 0) > 0 and not preserve_aux_handles)
        )
        if release_transformer:
            self.clear_transformer_cache()
        if release_non_transformer:
            self.clear_non_transformer_cache(
                preserve_aux_handles=preserve_aux_handles,
                preserve_stft_handles=preserve_stft_handles,
            )
        if release_transformer or release_non_transformer:
            gc.collect()
        return self._cache_release_summary(before, self.cache_handle_counts())

    def clear_stft_cache(self) -> dict[str, object]:
        before = self.cache_handle_counts()
        if before.get("stft_handles", 0) <= 0:
            return self._cache_release_summary(before, before)
        total_free = 0.0
        handle_count = 0
        for handle in self._stft_handle_cache.values():
            started = time.perf_counter()
            self.bridge.free(handle, label="stft_cache")
            total_free += time.perf_counter() - started
            handle_count += 1
        self._stft_handle_cache.clear()
        self._dynamic_stft_input_initialized.clear()
        gc_started = time.perf_counter()
        gc.collect()
        gc_sec = time.perf_counter() - gc_started
        self._record_free_profile("stft_cache", total_free, gc_sec, handle_count)
        return self._cache_release_summary(before, self.cache_handle_counts())

    def clear_irfft_cache(self) -> dict[str, object]:
        before = self.cache_handle_counts()
        if before.get("irfft_handles", 0) <= 0:
            return self._cache_release_summary(before, before)
        total_free = 0.0
        handle_count = 0
        for handle in self._irfft_handle_cache.values():
            started = time.perf_counter()
            self.bridge.free(handle, label="irfft_cache")
            total_free += time.perf_counter() - started
            handle_count += 1
        self._irfft_handle_cache.clear()
        gc_started = time.perf_counter()
        gc.collect()
        gc_sec = time.perf_counter() - gc_started
        self._record_free_profile("irfft_cache", total_free, gc_sec, handle_count)
        return self._cache_release_summary(before, self.cache_handle_counts())

    def clear_aux_handle_cache(self) -> dict[str, object]:
        before = self.cache_handle_counts()
        if before.get("aux_handles", 0) <= 0:
            return self._cache_release_summary(before, before)
        band_split_free = 0.0
        final_norm_free = 0.0
        mask_free = 0.0
        band_split_count = 0
        final_norm_count = 0
        mask_count = 0
        for handle in self._band_split_handle_cache.values():
            started = time.perf_counter()
            self.bridge.free(handle, label="aux_band_split_cache")
            band_split_free += time.perf_counter() - started
            band_split_count += 1
        self._band_split_handle_cache.clear()
        for handle in self._final_norm_handle_cache.values():
            started = time.perf_counter()
            self.bridge.free(handle, label="aux_final_norm_cache")
            final_norm_free += time.perf_counter() - started
            final_norm_count += 1
        self._final_norm_handle_cache.clear()
        for handle in self._mask_handle_cache.values():
            started = time.perf_counter()
            self.bridge.free(handle, label="aux_mask_cache")
            mask_free += time.perf_counter() - started
            mask_count += 1
        self._mask_handle_cache.clear()
        gc_started = time.perf_counter()
        gc.collect()
        gc_sec = time.perf_counter() - gc_started
        self._record_free_profile("aux_band_split_cache", band_split_free, gc_sec, band_split_count)
        self._record_free_profile("aux_final_norm_cache", final_norm_free, 0.0, final_norm_count)
        self._record_free_profile("aux_mask_cache", mask_free, 0.0, mask_count)
        return self._cache_release_summary(before, self.cache_handle_counts())

    def _compile_bridge(
            self,
            label: str,
            mil: str,
            weights: dict[str, bytes],
            input_bytes: int,
            output_bytes: int,
            use_load_cache: bool = True,
            guard_memory: bool = True,
    ):
        if guard_memory:
            self._guard_memory(f"{label}_before_compile")
        try:
            if use_load_cache:
                handle = self.bridge.compile(mil, weights, input_bytes, output_bytes)
            else:
                handle = self._compile_multi_inputs_outputs_uncached(
                    mil,
                    weights,
                    [input_bytes],
                    [output_bytes],
                )
        except Exception as exc:
            raise RuntimeError(f"{label} ANE compile failed") from exc
        if guard_memory:
            self._guard_memory(f"{label}_after_compile")
        return handle

    def _compile_bridge_multi_outputs(
            self,
            label: str,
            mil: str,
            weights: dict[str, bytes],
            input_bytes: int,
            output_bytes: list[int] | tuple[int, ...],
            use_load_cache: bool = True,
            guard_memory: bool = True,
    ):
        if guard_memory:
            self._guard_memory(f"{label}_before_compile")
        try:
            if use_load_cache:
                handle = self.bridge.compile_multi_outputs(mil, weights, input_bytes, output_bytes)
            else:
                handle = self._compile_multi_inputs_outputs_uncached(
                    mil,
                    weights,
                    [input_bytes],
                    output_bytes,
                )
        except Exception as exc:
            raise RuntimeError(f"{label} ANE compile failed") from exc
        if guard_memory:
            self._guard_memory(f"{label}_after_compile")
        return handle

    def _compile_multi_inputs_outputs_uncached(
            self,
            mil: str,
            weights: dict[str, bytes],
            input_bytes: list[int] | tuple[int, ...],
            output_bytes: list[int] | tuple[int, ...],
    ):
        previous_use_load_cache = bool(getattr(self.bridge, "use_load_cache", False))
        previous_env = {
            key: os.environ.get(key)
            for key in ("ANE_BRIDGE_LOAD_CACHE", "ANE_BRIDGE_TMPDIR")
        }
        self.bridge.use_load_cache = False
        for key in previous_env:
            os.environ.pop(key, None)
        try:
            return self.bridge.compile_multi_inputs_outputs(mil, weights, input_bytes, output_bytes)
        finally:
            self.bridge.use_load_cache = previous_use_load_cache
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _compile_persistent_bridge(
            self,
            cache: dict,
            key,
            label: str,
            mil: str,
            weights: dict[str, bytes],
            input_bytes: int,
            output_bytes: int,
            use_load_cache: bool = True,
    ):
        handle = cache.get(key)
        if handle is not None:
            return handle, 0.0, True
        started = time.perf_counter()
        handle = self._compile_bridge(
            label,
            mil,
            weights,
            input_bytes,
            output_bytes,
            use_load_cache=use_load_cache,
        )
        compile_sec = time.perf_counter() - started
        cache[key] = handle
        return handle, compile_sec, False

    @staticmethod
    def _profile_gc() -> float:
        started = time.perf_counter()
        gc.collect()
        return time.perf_counter() - started

    def _record_free_profile(self, family: str, free_sec: float, gc_sec: float, handles: int) -> None:
        if not family:
            family = "unknown"
        profile = getattr(self, "_free_profile_by_family", None)
        if not isinstance(profile, dict):
            profile = {}
            self._free_profile_by_family = profile
        bucket = profile.setdefault(
            family,
            {
                "free_sec": 0.0,
                "gc_sec": 0.0,
                "handles": 0,
                "calls": 0,
            },
        )
        bucket["free_sec"] = float(bucket.get("free_sec", 0.0) or 0.0) + float(free_sec)
        bucket["gc_sec"] = float(bucket.get("gc_sec", 0.0) or 0.0) + float(gc_sec)
        bucket["handles"] = int(bucket.get("handles", 0) or 0) + int(handles)
        bucket["calls"] = int(bucket.get("calls", 0) or 0) + 1

    def _profile_free_handle(self, handle, family: str = "unknown") -> tuple[float, float]:
        started = time.perf_counter()
        self.bridge.free(handle, label=family)
        free_sec = time.perf_counter() - started
        gc_sec = self._profile_gc()
        self._record_free_profile(family, free_sec, gc_sec, 1)
        return free_sec, gc_sec

    def _profile_free_handles(self, handles, family: str = "unknown") -> tuple[float, float]:
        total_free = 0.0
        handle_count = 0
        for handle in handles:
            started = time.perf_counter()
            self.bridge.free(handle, label=family)
            total_free += time.perf_counter() - started
            handle_count += 1
        defer_transformer_gc = (
            str(os.environ.get("PYMSS_PRIVATE_ANE_DEFER_TRANSFORMER_FREE_GC", "")).lower()
            in ("1", "true", "yes", "on")
            and str(family).startswith("transformer_")
        )
        gc_sec = 0.0 if defer_transformer_gc else self._profile_gc()
        self._record_free_profile(family, total_free, gc_sec, handle_count)
        return total_free, gc_sec

    def _compile_persistent_bridge_multi_outputs(
            self,
            cache: dict,
            key,
            label: str,
            mil: str,
            weights: dict[str, bytes],
            input_bytes: int,
            output_bytes: list[int] | tuple[int, ...],
            use_load_cache: bool = True,
    ):
        handle = cache.get(key)
        if handle is not None:
            return handle, 0.0, True
        started = time.perf_counter()
        handle = self._compile_bridge_multi_outputs(
            label,
            mil,
            weights,
            input_bytes,
            output_bytes,
            use_load_cache=use_load_cache,
        )
        compile_sec = time.perf_counter() - started
        cache[key] = handle
        return handle, compile_sec, False

    def _bridge_last_compile_profile(
            self,
            elapsed_sec: float,
            *,
            handle_cache_hit: bool = False,
    ) -> dict[str, object]:
        return _bridge_compile_profile_from_bridge(
            self.bridge,
            elapsed_sec,
            handle_cache_hit=handle_cache_hit,
        )

    def _compile_cached_stft_handle(self, out_start: int, tile_weights: np.ndarray, run_frames: int, batch: int = 1):
        key = (out_start, tile_weights.shape[0], run_frames, int(batch))
        handle = self._stft_handle_cache.get(key)
        if handle is not None:
            return handle, self._bridge_last_compile_profile(0.0, handle_cache_hit=True)
        started = time.perf_counter()
        with self._stft_bridge_qos_scope():
            handle = self._compile_bridge(
                f"stft_{out_start}_{tile_weights.shape[0]}_b{batch}",
                _stft_channel_seq_mil(run_frames, tile_weights.shape[0], STFT_N_FFT, batch),
                {"@model_path/weights/w.bin": _blob(tile_weights)},
                int(batch) * STFT_N_FFT * run_frames * 2,
                int(batch) * tile_weights.shape[0] * run_frames * 2,
                guard_memory=False,
            )
        elapsed_sec = time.perf_counter() - started
        profile = self._bridge_last_compile_profile(elapsed_sec)
        self._stft_handle_cache[key] = handle
        return handle, profile

    def _compile_cached_dynamic_stft_handle(self, run_frames: int, out_ch: int, batch: int = 1):
        key = ("dynamic", STFT_N_FFT, out_ch, run_frames, int(batch))
        handle = self._stft_handle_cache.get(key)
        if handle is not None:
            return handle, self._bridge_last_compile_profile(0.0, handle_cache_hit=True)
        started = time.perf_counter()
        mil = _stft_dynamic_matmul_mil(run_frames, out_ch, STFT_N_FFT, int(batch))
        input_bytes = int(batch) * STFT_N_FFT * (run_frames + out_ch) * 2
        output_bytes = int(batch) * out_ch * run_frames * 2
        use_load_cache = bool(getattr(self.module, "private_ane_load_cache", False))
        with self._stft_bridge_qos_scope():
            try:
                handle = self._compile_bridge(
                    f"stft_dynamic_f{run_frames}_{out_ch}_b{batch}",
                    mil,
                    {},
                    input_bytes,
                    output_bytes,
                    use_load_cache=use_load_cache,
                    guard_memory=False,
                )
            except RuntimeError:
                if not use_load_cache:
                    raise
                handle = self._compile_bridge(
                    f"stft_dynamic_f{run_frames}_{out_ch}_b{batch}",
                    mil,
                    {},
                    input_bytes,
                    output_bytes,
                    use_load_cache=False,
                    guard_memory=False,
                )
        elapsed_sec = time.perf_counter() - started
        profile = self._bridge_last_compile_profile(elapsed_sec)
        self._stft_handle_cache[key] = handle
        return handle, profile

    def warmup_ane_runtime(self, kind: str = "stft") -> dict[str, object]:
        total_started = time.perf_counter()
        handle = None
        profile: dict[str, object] = {}
        eval_sec = 0.0
        free_sec = 0.0
        if str(kind or "").strip().lower() == "client":
            client_started = time.perf_counter()
            client_mode = int(getattr(self.module, "private_ane_wakeup_client_mode", 0) or 0)
            client_sec = self.bridge.warmup_client(client_mode)
            return {
                "kind": "client",
                "mode": int(client_mode),
                "wall_sec": float(time.perf_counter() - total_started),
                "client_sec": float(client_sec),
                "python_client_wall_sec": float(time.perf_counter() - client_started),
            }
        wakeup_kind, mil, weights, input_shape, output_bytes = _ane_wakeup_spec(kind)
        input_bytes = int(np.prod(input_shape)) * 2
        try:
            compile_started = time.perf_counter()
            with self._stft_bridge_qos_scope():
                handle = self._compile_bridge(
                    f"ane_wakeup_{wakeup_kind}",
                    mil,
                    weights,
                    input_bytes,
                    output_bytes,
                    use_load_cache=bool(getattr(self.module, "private_ane_load_cache", False)),
                    guard_memory=False,
                )
            profile = self._bridge_last_compile_profile(time.perf_counter() - compile_started)
            x = np.zeros(input_shape, dtype=np.float16)
            write_sec = self.bridge.write_input_raw(handle, x)
            eval_started = time.perf_counter()
            self._stft_bridge_eval(handle)
            eval_sec = time.perf_counter() - eval_started
            free_started = time.perf_counter()
            self.bridge.free(handle)
            free_sec = time.perf_counter() - free_started
            handle = None
            return {
                "kind": wakeup_kind,
                "wall_sec": float(time.perf_counter() - total_started),
                "input_bytes": int(input_bytes),
                "output_bytes": int(output_bytes),
                "bridge_qos": self._stft_bridge_qos_label(),
                "write_sec": float(write_sec),
                "eval_sec": float(eval_sec),
                "free_sec": float(free_sec),
                "bridge_atomic_writes": self._stft_bridge_atomic_writes_label(),
                **profile,
            }
        finally:
            if handle is not None:
                free_started = time.perf_counter()
                self.bridge.free(handle)
                free_sec = time.perf_counter() - free_started

    def _initialize_dynamic_stft_input(
            self,
            handle,
            dynamic_weights: np.ndarray | None,
            run_frames: int,
            out_ch: int,
            batch: int = 1,
    ) -> tuple[float, bool]:
        handle_id = int(handle)
        if handle_id in self._dynamic_stft_input_initialized:
            return 0.0, True
        if dynamic_weights is None:
            try:
                write_sec = self.bridge.fill_stft_dynamic_weights_input_fp16(
                    handle,
                    n_fft=STFT_N_FFT,
                    frames=run_frames,
                    out_ch=out_ch,
                    batches=int(batch),
                )
                self._dynamic_stft_input_initialized.add(handle_id)
                return write_sec, False
            except (AttributeError, RuntimeError):
                dynamic_weights = _stft_dynamic_weight_groups()[0][1]
        dynamic_weights = np.ascontiguousarray(dynamic_weights, dtype=np.float16)
        out_ch = int(out_ch)
        write_sec = 0.0
        batch_stride_bytes = STFT_N_FFT * (run_frames + out_ch) * 2
        for batch_index in range(int(batch)):
            write_sec += self.bridge.write_input_rows_raw(
                handle,
                dynamic_weights,
                rows=STFT_N_FFT,
                row_bytes=out_ch * 2,
                src_row_stride_bytes=int(dynamic_weights.strides[0]),
                dst_offset_bytes=batch_index * batch_stride_bytes + run_frames * 2,
                dst_row_stride_bytes=(run_frames + out_ch) * 2,
            )
        self._dynamic_stft_input_initialized.add(handle_id)
        return write_sec, False

    def _compile_cached_fused_stft_handle(
            self,
            tile_ranges: tuple[tuple[int, int], ...],
            run_frames: int,
            batch: int = 1,
    ):
        tile_channels = tuple(out_end - out_start for out_start, out_end in tile_ranges)
        group_start = tile_ranges[0][0]
        group_end = tile_ranges[-1][1]
        key = ("fused", group_start, group_end, tile_channels, run_frames, int(batch))
        handle = self._stft_handle_cache.get(key)
        if handle is not None:
            return handle, self._bridge_last_compile_profile(0.0, handle_cache_hit=True)
        started = time.perf_counter()
        weights = {
            f"@model_path/weights/w{tile_index}.bin": _blob(_stft_dft_weight_tile(out_start, out_end))
            for tile_index, (out_start, out_end) in enumerate(tile_ranges)
        }
        output_bytes = int(batch) * sum(tile_channels) * run_frames * 2
        with self._stft_bridge_qos_scope():
            handle = self._compile_bridge(
                f"stft_fused_{group_start}_{group_end}_b{batch}",
                _stft_channel_seq_fused_mil(tile_channels, run_frames, STFT_N_FFT, batch),
                weights,
                int(batch) * STFT_N_FFT * run_frames * 2,
                output_bytes,
                guard_memory=False,
            )
        elapsed_sec = time.perf_counter() - started
        profile = self._bridge_last_compile_profile(elapsed_sec)
        self._stft_handle_cache[key] = handle
        return handle, profile

    def preload_stft_handles(self) -> dict[str, object]:
        wall_started = time.perf_counter()
        weight_groups_sec = 0.0
        total_compile = 0.0
        total_load_cache = 0.0
        total_load_cache_attempt = 0.0
        total_load_cache_miss = 0.0
        total_load_or_compile = 0.0
        total_bridge_load_or_compile = 0.0
        bridge_profile_totals: dict[str, float] = {}
        total_static_write = 0.0
        total_static_write_hits = 0
        cache_hits = 0
        run_frames = self._stft_frame_tile()
        handle_batch = 2 if self._batch_stft_istft_channels() else 1
        weight_cache_hit = False
        weight_cache_sec = 0.0
        before_bridge_hits = int(getattr(self.bridge, "load_cache_hits", 0))
        before_bridge_misses = int(getattr(self.bridge, "load_cache_misses", 0))
        fused_groups = 0
        dynamic_groups = 0
        dynamic_weight_groups = ()
        if self._dynamic_stft():
            weights_started = time.perf_counter()
            dynamic_weight_groups, weight_cache_hit, weight_cache_sec = self._dynamic_stft_weight_groups()
            weight_groups_sec += time.perf_counter() - weights_started
            for _row_indices, weights in dynamic_weight_groups:
                dynamic_groups += 1
                dynamic_out_ch = int(weights.shape[1]) if weights is not None else len(_row_indices)
                handle, profile = self._compile_cached_dynamic_stft_handle(
                    run_frames,
                    dynamic_out_ch,
                    handle_batch,
                )
                static_write_sec, static_write_hit = self._initialize_dynamic_stft_input(
                    handle,
                    weights,
                    run_frames,
                    dynamic_out_ch,
                    handle_batch,
                )
                total_static_write += static_write_sec
                total_static_write_hits += int(static_write_hit)
                total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
                total_load_cache += float(profile.get("load_cache_sec", 0.0) or 0.0)
                total_load_cache_attempt += float(profile.get("load_cache_attempt_sec", 0.0) or 0.0)
                total_load_cache_miss += float(profile.get("load_cache_miss_sec", 0.0) or 0.0)
                total_load_or_compile += float(profile.get("load_or_compile_sec", 0.0) or 0.0)
                total_bridge_load_or_compile += float(profile.get("bridge_load_or_compile_sec", 0.0) or 0.0)
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                if bool(profile.get("handle_cache_hit", False)):
                    cache_hits += 1
        elif self._fused_stft():
            for tile_ranges in _group_stft_output_tiles(self._fused_stft_max_outputs()):
                fused_groups += 1
                _, profile = self._compile_cached_fused_stft_handle(tile_ranges, run_frames, handle_batch)
                total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
                total_load_cache += float(profile.get("load_cache_sec", 0.0) or 0.0)
                total_load_cache_attempt += float(profile.get("load_cache_attempt_sec", 0.0) or 0.0)
                total_load_cache_miss += float(profile.get("load_cache_miss_sec", 0.0) or 0.0)
                total_load_or_compile += float(profile.get("load_or_compile_sec", 0.0) or 0.0)
                total_bridge_load_or_compile += float(profile.get("bridge_load_or_compile_sec", 0.0) or 0.0)
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                if bool(profile.get("handle_cache_hit", False)):
                    cache_hits += 1
        else:
            for out_start, out_end in _stft_output_tile_ranges():
                tile_weights = _stft_dft_weight_tile(out_start, out_end)
                _, profile = self._compile_cached_stft_handle(out_start, tile_weights, run_frames, handle_batch)
                total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
                total_load_cache += float(profile.get("load_cache_sec", 0.0) or 0.0)
                total_load_cache_attempt += float(profile.get("load_cache_attempt_sec", 0.0) or 0.0)
                total_load_cache_miss += float(profile.get("load_cache_miss_sec", 0.0) or 0.0)
                total_load_or_compile += float(profile.get("load_or_compile_sec", 0.0) or 0.0)
                total_bridge_load_or_compile += float(profile.get("bridge_load_or_compile_sec", 0.0) or 0.0)
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                if bool(profile.get("handle_cache_hit", False)):
                    cache_hits += 1
        after_bridge_hits = int(getattr(self.bridge, "load_cache_hits", 0))
        after_bridge_misses = int(getattr(self.bridge, "load_cache_misses", 0))
        timing_out_tile = (
            max((weights.shape[1] if weights is not None else len(row_indices)) for row_indices, weights in dynamic_weight_groups)
            if self._dynamic_stft()
            else STFT_OUT_TILE
        )
        timing = {
            "stage": "private_ane_stft_handle_preload",
            "bridge_qos": self._stft_bridge_qos_label(),
            "bridge_atomic_writes": self._stft_bridge_atomic_writes_label(),
            "weight_groups_sec": float(weight_groups_sec),
            "compile_sec": float(total_compile),
            "cold_compile_sec": float(total_compile),
            "load_cache_sec": float(total_load_cache),
            "load_cache_attempt_sec": float(total_load_cache_attempt),
            "load_cache_miss_sec": float(total_load_cache_miss),
            "load_or_compile_sec": float(total_load_or_compile),
            "bridge_load_or_compile_sec": float(total_bridge_load_or_compile),
            "static_bridge_write_sec": float(total_static_write),
            "static_bridge_write_hits": int(total_static_write_hits),
            "weight_cache_hit": bool(weight_cache_hit),
            "weight_cache_sec": float(weight_cache_sec),
            "wall_sec": float(time.perf_counter() - wall_started),
            "handles": int(len(self._stft_handle_cache)),
            "handle_cache_hits": int(cache_hits),
            "load_cache_hits_delta": int(after_bridge_hits - before_bridge_hits),
            "load_cache_misses_delta": int(after_bridge_misses - before_bridge_misses),
            "out_tile": int(timing_out_tile),
            "frame_tile": run_frames,
            "frames": TIME_SEQ,
            "batch_channels": bool(self._batch_stft_istft_channels()),
            "dynamic": bool(self._dynamic_stft()),
            "dynamic_out_ch": int(STFT_FREQ_BINS * 2) if self._dynamic_stft() else 0,
            "dynamic_computed_out_ch": int(timing_out_tile) if self._dynamic_stft() else 0,
            "dynamic_max_outputs": int(self._dynamic_stft_max_outputs()) if self._dynamic_stft() else 0,
            "dynamic_zero_rows": 2 if self._dynamic_stft() else 0,
            "dynamic_groups": int(dynamic_groups),
            "fused": bool(self._fused_stft()),
            "fused_groups": int(fused_groups),
            "fused_max_outputs": int(self._fused_stft_max_outputs()) if self._fused_stft() else 1,
        }
        timing.update(bridge_profile_totals)
        self.last_stft_preload_timing = timing
        return timing

    def _compile_cached_irfft_handle(self, out_start: int, tile_weights: np.ndarray, run_frames: int, batch: int = 1):
        key = (out_start, tile_weights.shape[0], run_frames, int(batch))
        handle = self._irfft_handle_cache.get(key)
        if handle is not None:
            return handle, self._bridge_last_compile_profile(0.0, handle_cache_hit=True)
        started = time.perf_counter()
        handle = self._compile_bridge(
            f"irfft_{out_start}_{tile_weights.shape[0]}_b{batch}",
            _irfft_channel_seq_mil(run_frames, tile_weights.shape[0], STFT_FREQ_BINS * 2, batch),
            {"@model_path/weights/w.bin": _blob(tile_weights)},
            int(batch) * STFT_FREQ_BINS * 2 * run_frames * 2,
            int(batch) * tile_weights.shape[0] * run_frames * 2,
        )
        compile_sec = time.perf_counter() - started
        profile = self._bridge_last_compile_profile(compile_sec)
        self._irfft_handle_cache[key] = handle
        return handle, profile

    def run_stft_channel_seq(self, raw_audio: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
        wall_started = time.perf_counter()
        prep_started = time.perf_counter()
        raw_audio = np.ascontiguousarray(raw_audio, dtype=np.float32)
        if raw_audio.shape != (2, 480000):
            raise ValueError(f"private_ane STFT expects stereo chunk shape (2,480000), got {raw_audio.shape}")
        pad = STFT_N_FFT // 2
        padded = np.pad(raw_audio, ((0, 0), (pad, pad)), mode="reflect")
        frames = 1 + (padded.shape[-1] - STFT_N_FFT) // STFT_HOP
        if frames != TIME_SEQ:
            raise ValueError(f"private_ane STFT expected {TIME_SEQ} frames, got {frames}")
        framed = np.lib.stride_tricks.sliding_window_view(padded, STFT_N_FFT, axis=-1)[:, ::STFT_HOP, :]
        stft_input_dtype = np.float16
        x = np.ascontiguousarray(
            framed.transpose(0, 2, 1).reshape(2, STFT_N_FFT, 1, TIME_SEQ),
            dtype=stft_input_dtype,
        )
        prep_sec = time.perf_counter() - prep_started
        weights_started = time.perf_counter()
        weight_cache_hit = False
        weight_cache_sec = 0.0
        if self._dynamic_stft():
            dynamic_weight_groups, weight_cache_hit, weight_cache_sec = self._dynamic_stft_weight_groups()
        else:
            dynamic_weight_groups = ()
        weight_groups_sec = time.perf_counter() - weights_started
        dynamic_compact_rows = (
            dynamic_weight_groups[0][0]
            if (
                self._dynamic_stft()
                and len(dynamic_weight_groups) == 1
                and len(dynamic_weight_groups[0][0]) == STFT_FREQ_BINS * 2 - 2
            )
            else None
        )
        dynamic_compact = dynamic_compact_rows is not None
        out_rows = len(dynamic_compact_rows) if dynamic_compact_rows is not None else STFT_FREQ_BINS * 2
        if dynamic_compact:
            out = np.empty((1, STFT_FREQ_BINS * 2, TIME_SEQ, 2), dtype=np.float32)
            out[0, :2, :, 1] = 0.0
            out[0, -2:, :, 1] = 0.0
        else:
            out = np.empty((2, out_rows, TIME_SEQ), dtype=np.float16)
            if self._dynamic_stft():
                out[:, 1, :] = 0.0
                out[:, -1, :] = 0.0
        total_compile = 0.0
        total_load_cache = 0.0
        total_load_cache_attempt = 0.0
        total_load_cache_miss = 0.0
        total_load_or_compile = 0.0
        total_bridge_load_or_compile = 0.0
        bridge_profile_totals: dict[str, float] = {}
        total_handle_cache_hits = 0
        total_eval = 0.0
        total_ane_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        total_bridge_write = 0.0
        total_bridge_read = 0.0
        total_static_write = 0.0
        total_static_write_hits = 0
        batch_channels = self._batch_stft_istft_channels()
        run_frames = self._stft_frame_tile()
        handle_batch = x.shape[0] if batch_channels else 1
        before_bridge_hits = int(getattr(self.bridge, "load_cache_hits", 0))
        before_bridge_misses = int(getattr(self.bridge, "load_cache_misses", 0))
        fused_groups = 0

        def _frame_tile(frame_start: int, frame_end: int):
            nonlocal total_pack
            valid = frame_end - frame_start
            if valid == run_frames:
                return x[:, :, :, frame_start:frame_end], valid
            pack_started = time.perf_counter()
            tile_x = np.zeros((2, STFT_N_FFT, 1, run_frames), dtype=x.dtype)
            tile_x[..., :valid] = x[:, :, :, frame_start:frame_end]
            total_pack += time.perf_counter() - pack_started
            return tile_x, valid

        def _write_stft_rows(y_rows: np.ndarray, out_start: int, out_end: int, frame_start: int, frame_end: int, channel: int):
            nonlocal total_write
            valid_rows = out_end - out_start
            valid = frame_end - frame_start
            write_started = time.perf_counter()
            out[channel, out_start:out_end, frame_start:frame_end] = y_rows[:valid_rows, :valid]
            total_write += time.perf_counter() - write_started

        def _write_dynamic_stft_rows(y_rows: np.ndarray, row_indices: tuple[int, ...], frame_start: int, frame_end: int, channel: int):
            nonlocal total_write
            valid = frame_end - frame_start
            write_started = time.perf_counter()
            if dynamic_compact:
                out[0, channel, frame_start:frame_end, 0] = y_rows[0, :valid]
                rows_2_to_nyquist_real = y_rows[1:len(row_indices), :valid]
                out[0, 2 + channel::2, frame_start:frame_end, 0] = rows_2_to_nyquist_real[0::2]
                out[
                    0,
                    2 + channel:(STFT_FREQ_BINS - 1) * 2 + channel:2,
                    frame_start:frame_end,
                    1,
                ] = rows_2_to_nyquist_real[1::2]
            else:
                out[channel, row_indices, frame_start:frame_end] = y_rows[:len(row_indices), :valid]
            total_write += time.perf_counter() - write_started

        dynamic_groups = 0
        if self._dynamic_stft():
            eval_started = time.perf_counter()
            for row_indices, dynamic_weights in dynamic_weight_groups:
                dynamic_groups += 1
                dynamic_out_ch = int(dynamic_weights.shape[1]) if dynamic_weights is not None else len(row_indices)
                handle, profile = self._compile_cached_dynamic_stft_handle(
                    run_frames,
                    dynamic_out_ch,
                    handle_batch,
                )
                static_write_sec, static_write_hit = self._initialize_dynamic_stft_input(
                    handle,
                    dynamic_weights,
                    run_frames,
                    dynamic_out_ch,
                    handle_batch,
                )
                total_bridge_write += static_write_sec
                total_static_write += static_write_sec
                total_static_write_hits += int(static_write_hit)
                total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
                total_load_cache += float(profile.get("load_cache_sec", 0.0) or 0.0)
                total_load_cache_attempt += float(profile.get("load_cache_attempt_sec", 0.0) or 0.0)
                total_load_cache_miss += float(profile.get("load_cache_miss_sec", 0.0) or 0.0)
                total_load_or_compile += float(profile.get("load_or_compile_sec", 0.0) or 0.0)
                total_bridge_load_or_compile += float(profile.get("bridge_load_or_compile_sec", 0.0) or 0.0)
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                total_handle_cache_hits += int(bool(profile.get("handle_cache_hit", False)))
                if batch_channels:
                    tail_input = np.empty((2, STFT_N_FFT, run_frames), dtype=np.float16)
                    for frame_start in range(0, TIME_SEQ, run_frames):
                        frame_end = min(frame_start + run_frames, TIME_SEQ)
                        valid = frame_end - frame_start
                        if valid == run_frames:
                            act_batch = x[:, :, 0, frame_start:frame_end]
                            row_bytes = run_frames * 2
                        else:
                            pack_started = time.perf_counter()
                            tail_input[:, :, valid:] = 0.0
                            tail_input[:, :, :valid] = x[:, :, 0, frame_start:frame_end]
                            total_pack += time.perf_counter() - pack_started
                            act_batch = tail_input
                            row_bytes = run_frames * 2
                        batch_stride_bytes = STFT_N_FFT * (run_frames + dynamic_out_ch) * 2
                        for channel_index in range(2):
                            act_rows = act_batch[channel_index]
                            total_bridge_write += self.bridge.write_input_rows_raw(
                                handle,
                                act_rows,
                                rows=STFT_N_FFT,
                                row_bytes=row_bytes,
                                src_row_stride_bytes=int(act_rows.strides[0]),
                                dst_offset_bytes=channel_index * batch_stride_bytes,
                                dst_row_stride_bytes=(run_frames + dynamic_out_ch) * 2,
                            )
                        ane_started = time.perf_counter()
                        self._stft_bridge_eval(handle)
                        total_ane_eval += time.perf_counter() - ane_started
                        y, read_sec = self.bridge.read_output_raw(
                            handle,
                            (2, dynamic_out_ch, 1, run_frames),
                            dtype=np.float16,
                        )
                        total_bridge_read += read_sec
                        for channel_index in range(2):
                            _write_dynamic_stft_rows(
                                y[channel_index, :, 0, :],
                                row_indices,
                                frame_start,
                                frame_end,
                                channel_index,
                            )
                else:
                    tail_input = np.empty((STFT_N_FFT, run_frames), dtype=np.float16)
                    for channel_index in range(2):
                        for frame_start in range(0, TIME_SEQ, run_frames):
                            frame_end = min(frame_start + run_frames, TIME_SEQ)
                            valid = frame_end - frame_start
                            if valid == run_frames:
                                act_rows = x[channel_index, :, 0, frame_start:frame_end]
                                row_bytes = run_frames * 2
                            else:
                                pack_started = time.perf_counter()
                                tail_input[:, valid:] = 0.0
                                tail_input[:, :valid] = x[channel_index, :, 0, frame_start:frame_end]
                                total_pack += time.perf_counter() - pack_started
                                act_rows = tail_input
                                row_bytes = run_frames * 2
                            total_bridge_write += self.bridge.write_input_rows_raw(
                                handle,
                                act_rows,
                                rows=STFT_N_FFT,
                                row_bytes=row_bytes,
                                src_row_stride_bytes=int(act_rows.strides[0]),
                                dst_offset_bytes=0,
                                dst_row_stride_bytes=(run_frames + dynamic_out_ch) * 2,
                            )
                            ane_started = time.perf_counter()
                            self._stft_bridge_eval(handle)
                            total_ane_eval += time.perf_counter() - ane_started
                            y, read_sec = self.bridge.read_output_raw(
                                handle,
                                (1, dynamic_out_ch, 1, run_frames),
                                dtype=np.float16,
                            )
                            total_bridge_read += read_sec
                            _write_dynamic_stft_rows(
                                y[0, :, 0, :],
                                row_indices,
                                frame_start,
                                frame_end,
                                channel_index,
                            )
            total_eval += time.perf_counter() - eval_started
        elif self._fused_stft():
            for tile_ranges in _group_stft_output_tiles(self._fused_stft_max_outputs()):
                fused_groups += 1
                handle, profile = self._compile_cached_fused_stft_handle(tile_ranges, run_frames, handle_batch)
                total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
                total_load_cache += float(profile.get("load_cache_sec", 0.0) or 0.0)
                total_load_cache_attempt += float(profile.get("load_cache_attempt_sec", 0.0) or 0.0)
                total_load_cache_miss += float(profile.get("load_cache_miss_sec", 0.0) or 0.0)
                total_load_or_compile += float(profile.get("load_or_compile_sec", 0.0) or 0.0)
                total_bridge_load_or_compile += float(profile.get("bridge_load_or_compile_sec", 0.0) or 0.0)
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                total_handle_cache_hits += int(bool(profile.get("handle_cache_hit", False)))
                tile_widths = tuple(out_end - out_start for out_start, out_end in tile_ranges)
                tile_offsets = (0, *np.cumsum(np.array(tile_widths, dtype=np.int64)).tolist())
                output_shape = (handle_batch, int(sum(tile_widths)), 1, run_frames)
                eval_started = time.perf_counter()
                for frame_start in range(0, TIME_SEQ, run_frames):
                    frame_end = min(frame_start + run_frames, TIME_SEQ)
                    tile_x, valid = _frame_tile(frame_start, frame_end)
                    if batch_channels:
                        y = self._stft_bridge_run(handle, tile_x, output_shape)
                        write_started = time.perf_counter()
                        for tile_index, (out_start, out_end) in enumerate(tile_ranges):
                            local_start = int(tile_offsets[tile_index])
                            local_end = int(tile_offsets[tile_index + 1])
                            for channel_index in range(2):
                                _write_stft_rows(
                                    y[channel_index, local_start:local_end, 0, :],
                                    out_start,
                                    out_end,
                                    frame_start,
                                    frame_end,
                                    channel_index,
                                )
                    else:
                        for channel_index in range(2):
                            y = self._stft_bridge_run(
                                handle,
                                tile_x[channel_index:channel_index + 1],
                                output_shape,
                            )
                            for tile_index, (out_start, out_end) in enumerate(tile_ranges):
                                local_start = int(tile_offsets[tile_index])
                                local_end = int(tile_offsets[tile_index + 1])
                                _write_stft_rows(
                                    y[0, local_start:local_end, 0, :],
                                    out_start,
                                    out_end,
                                    frame_start,
                                    frame_end,
                                    channel_index,
                                )
                total_eval += time.perf_counter() - eval_started
        else:
            for out_start, out_end in _stft_output_tile_ranges():
                tile_weights = _stft_dft_weight_tile(out_start, out_end)
                handle, profile = self._compile_cached_stft_handle(out_start, tile_weights, run_frames, handle_batch)
                total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
                total_load_cache += float(profile.get("load_cache_sec", 0.0) or 0.0)
                total_load_cache_attempt += float(profile.get("load_cache_attempt_sec", 0.0) or 0.0)
                total_load_cache_miss += float(profile.get("load_cache_miss_sec", 0.0) or 0.0)
                total_load_or_compile += float(profile.get("load_or_compile_sec", 0.0) or 0.0)
                total_bridge_load_or_compile += float(profile.get("bridge_load_or_compile_sec", 0.0) or 0.0)
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                total_handle_cache_hits += int(bool(profile.get("handle_cache_hit", False)))
                eval_started = time.perf_counter()
                for frame_start in range(0, TIME_SEQ, run_frames):
                    frame_end = min(frame_start + run_frames, TIME_SEQ)
                    tile_x, valid = _frame_tile(frame_start, frame_end)
                    if batch_channels:
                        y = self._stft_bridge_run(handle, tile_x, (2, tile_weights.shape[0], 1, run_frames))
                        for channel_index in range(2):
                            _write_stft_rows(
                                y[channel_index, :, 0, :],
                                out_start,
                                out_end,
                                frame_start,
                                frame_end,
                                channel_index,
                            )
                    else:
                        for channel_index in range(2):
                            y = self._stft_bridge_run(
                                handle,
                                tile_x[channel_index:channel_index + 1],
                                (1, tile_weights.shape[0], 1, run_frames),
                            )
                            _write_stft_rows(y[0, :, 0, :], out_start, out_end, frame_start, frame_end, channel_index)
                total_eval += time.perf_counter() - eval_started
        after_bridge_hits = int(getattr(self.bridge, "load_cache_hits", 0))
        after_bridge_misses = int(getattr(self.bridge, "load_cache_misses", 0))
        reshape_started = time.perf_counter()
        if dynamic_compact:
            stft_repr = out
        else:
            stft_repr = (
                out.reshape(2, STFT_FREQ_BINS, 2, TIME_SEQ)
                .transpose(1, 0, 3, 2)
                .reshape(1, STFT_FREQ_BINS * 2, TIME_SEQ, 2)
                .astype(np.float32, copy=False)
            )
        reshape_sec = time.perf_counter() - reshape_started
        timing_out_tile = (
            max((weights.shape[1] if weights is not None else len(row_indices)) for row_indices, weights in dynamic_weight_groups)
            if self._dynamic_stft()
            else STFT_OUT_TILE
        )
        timing = {
            "compile_sec": float(total_compile),
            "cold_compile_sec": float(total_compile),
            "load_cache_sec": float(total_load_cache),
            "load_cache_attempt_sec": float(total_load_cache_attempt),
            "load_cache_miss_sec": float(total_load_cache_miss),
            "load_or_compile_sec": float(total_load_or_compile),
            "bridge_load_or_compile_sec": float(total_bridge_load_or_compile),
            "weight_groups_sec": float(weight_groups_sec),
            "weight_cache_hit": bool(weight_cache_hit),
            "weight_cache_sec": float(weight_cache_sec),
            "handle_cache_hits": int(total_handle_cache_hits),
            "eval_sec": float(total_eval),
            "ane_eval_sec": float(total_ane_eval),
            "bridge_write_sec": float(total_bridge_write),
            "static_bridge_write_sec": float(total_static_write),
            "static_bridge_write_hits": int(total_static_write_hits),
            "bridge_read_sec": float(total_bridge_read),
            "prep_sec": float(prep_sec),
            "pack_sec": float(total_pack),
            "write_sec": float(total_write),
            "reshape_sec": float(reshape_sec),
            "wall_sec": float(time.perf_counter() - wall_started),
            "out_tile": int(timing_out_tile),
            "frame_tile": run_frames,
            "frames": TIME_SEQ,
            "batch_channels": bool(batch_channels),
            "load_cache_hits_delta": int(after_bridge_hits - before_bridge_hits),
            "load_cache_misses_delta": int(after_bridge_misses - before_bridge_misses),
            "dynamic": bool(self._dynamic_stft()),
            "dynamic_out_ch": int(STFT_FREQ_BINS * 2) if self._dynamic_stft() else 0,
            "dynamic_computed_out_ch": int(timing_out_tile) if self._dynamic_stft() else 0,
            "dynamic_max_outputs": int(self._dynamic_stft_max_outputs()) if self._dynamic_stft() else 0,
            "dynamic_zero_rows": 2 if self._dynamic_stft() else 0,
            "dynamic_compact_rows": bool(dynamic_compact),
            "dynamic_groups": int(dynamic_groups),
            "fused": bool(self._fused_stft()),
            "fused_groups": int(fused_groups),
            "fused_max_outputs": int(self._fused_stft_max_outputs()) if self._fused_stft() else 1,
            "stage": "private_ane_dft_cpu_reflect_pad_frame",
            "bridge_qos": self._stft_bridge_qos_label(),
            "bridge_atomic_writes": self._stft_bridge_atomic_writes_label(),
        }
        timing.update(bridge_profile_totals)
        self.last_stft_timing = timing
        return stft_repr, timing

    def run_irfft_channel_seq(self, stft_repr: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
        wall_started = time.perf_counter()
        prep_started = time.perf_counter()
        stft_repr = np.ascontiguousarray(stft_repr, dtype=np.float32)
        if stft_repr.shape != (2, STFT_FREQ_BINS, TIME_SEQ, 2):
            raise ValueError(f"private_ane ISTFT expects (2,{STFT_FREQ_BINS},{TIME_SEQ},2), got {stft_repr.shape}")
        x = np.ascontiguousarray(
            stft_repr.transpose(0, 1, 3, 2).reshape(2, STFT_FREQ_BINS * 2, 1, TIME_SEQ),
            dtype=np.float16,
        )
        prep_sec = time.perf_counter() - prep_started
        out = np.empty((2, TIME_SEQ, STFT_N_FFT), dtype=np.float16)
        total_compile = 0.0
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        bridge_profile_totals: dict[str, float] = {}
        batch_channels = self._batch_stft_istft_channels()
        for out_start in range(0, STFT_N_FFT, ISTFT_OUT_TILE):
            out_end = min(out_start + ISTFT_OUT_TILE, STFT_N_FFT)
            tile_weights = _irfft_weight_tile(out_start, out_end)
            run_frames = min(ISTFT_FRAME_TILE, TIME_SEQ)
            handle_batch = x.shape[0] if batch_channels else 1
            handle, profile = self._compile_cached_irfft_handle(out_start, tile_weights, run_frames, handle_batch)
            total_compile += float(profile.get("compile_sec", 0.0) or 0.0)
            _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
            eval_started = time.perf_counter()
            for frame_start in range(0, TIME_SEQ, ISTFT_FRAME_TILE):
                frame_end = min(frame_start + ISTFT_FRAME_TILE, TIME_SEQ)
                valid = frame_end - frame_start
                if valid == run_frames:
                    tile_x = x[:, :, :, frame_start:frame_end]
                else:
                    pack_started = time.perf_counter()
                    tile_x = np.zeros((2, STFT_FREQ_BINS * 2, 1, run_frames), dtype=np.float16)
                    tile_x[..., :valid] = x[:, :, :, frame_start:frame_end]
                    total_pack += time.perf_counter() - pack_started
                if batch_channels:
                    y = self.bridge.run(handle, tile_x, (2, tile_weights.shape[0], 1, run_frames))
                    write_started = time.perf_counter()
                    out[:, frame_start:frame_end, out_start:out_end] = y[:, :, 0, :valid].transpose(0, 2, 1)
                    total_write += time.perf_counter() - write_started
                else:
                    for channel_index in range(2):
                        y = self.bridge.run(
                            handle,
                            tile_x[channel_index:channel_index + 1],
                            (1, tile_weights.shape[0], 1, run_frames),
                        )
                        write_started = time.perf_counter()
                        out[channel_index, frame_start:frame_end, out_start:out_end] = (
                            y[..., :valid].reshape(tile_weights.shape[0], valid).T
                        )
                        total_write += time.perf_counter() - write_started
            total_eval += time.perf_counter() - eval_started
        timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "prep_sec": float(prep_sec),
            "pack_sec": float(total_pack),
            "write_sec": float(total_write),
            "wall_sec": float(time.perf_counter() - wall_started),
            "out_tile": ISTFT_OUT_TILE,
            "frame_tile": ISTFT_FRAME_TILE,
            "frames": TIME_SEQ,
            "batch_channels": bool(batch_channels),
            "stage": "private_ane_irfft_cpu_overlap_add",
        }
        timing.update(bridge_profile_totals)
        self.last_istft_timing = timing
        return out.astype(np.float32), timing

    def _compile_axis_handles(
            self,
            axis: str,
            layer_index: int,
            batch: int,
            seq: int,
            valid_seq: int,
            *,
            fuse_residual: bool | None = None,
    ):
        unpadded_freq_probe = (
            axis == "freq"
            and seq == FREQ_SEQ
            and valid_seq == FREQ_SEQ
            and self._direct_time_to_freq_unpadded()
        )
        surface_seq = FREQ_PAD if unpadded_freq_probe else None
        if not self._batch_axis_attention_pre_supported(axis, batch, seq) and not unpadded_freq_probe:
            raise RuntimeError(
                "private_ane batch-axis transformer eval is not supported for "
                f"axis={axis}, batch={batch}, seq={seq}; current ANE attention_pre "
                "templates fail compilation for multi-chunk shapes"
            )
        attn, ffn = _block_modules(self.module, axis, layer_index)
        dummy_bytes = batch * DIM * seq * 2
        effective_fuse_residual = self._fuse_residual() if fuse_residual is None else bool(fuse_residual)
        def memory_guard(stage: str) -> None:
            self._guard_memory(f"{axis}_layer{layer_index}_{stage}")
        attention_pre_mil = self._attention_pre_mil_for_axis(axis, layer_index, batch, seq, valid_seq)

        if self._fuse_gate_ffn_axis(axis, batch, seq):
            return _compile_fused_gate_ffn_block(
                self.bridge,
                attn,
                ffn,
                batch,
                seq,
                valid_seq,
                self._gelu_mode(),
                dummy_bytes,
                memory_guard=memory_guard,
                attention_pre_mil=attention_pre_mil,
            )
        return _compile_block(
            self.bridge,
            attn,
            ffn,
            batch,
            seq,
            valid_seq,
            self._gelu_mode(),
            dummy_bytes,
            memory_guard=memory_guard,
            fuse_residual=effective_fuse_residual,
            two_input_gate=self._two_input_gate(),
            attention_pre_mil=attention_pre_mil,
            surface_seq=surface_seq,
        )

    def _compile_axis_handles_cached(
            self,
            axis: str,
            layer_index: int,
            segment_index: int,
            batch: int,
            seq: int,
            valid_seq: int,
            *,
            fuse_residual: bool | None = None,
    ):
        cache_limit = self._segment_cache_limit()
        gelu_mode = self._gelu_mode()
        effective_fuse_residual = self._fuse_residual() if fuse_residual is None else bool(fuse_residual)
        fuse_gate_ffn = self._fuse_gate_ffn_axis(axis, batch, seq)
        tiled_attention_pre = self._tiled_attention_pre_for_shape(
            axis,
            layer_index,
            batch,
            seq,
            valid_seq,
        )
        tiled_q_chunk = self._tiled_time_attention_pre_q_chunk() if tiled_attention_pre else 0
        surface_seq = (
            FREQ_PAD
            if (
                axis == "freq"
                and seq == FREQ_SEQ
                and valid_seq == FREQ_SEQ
                and self._direct_time_to_freq_unpadded()
            )
            else None
        )
        cache_key = (
            "layerwise",
            axis,
            layer_index,
            batch,
            seq,
            valid_seq,
            gelu_mode,
            effective_fuse_residual,
            fuse_gate_ffn,
            self._two_input_gate(),
            self._surface_handoff_gate_ffn(),
            tiled_attention_pre,
            tiled_q_chunk,
            surface_seq,
        )
        if cache_limit > 0 and segment_index < cache_limit and cache_key in self._block_cache:
            self._guard_memory(f"{axis}_layer{layer_index}_cache_hit", segment_index)
            cache_profile = {
                "load_or_compile_wall_sec": 0.0,
                "compile_wall_sec": 0.0,
                "pre_compile_sec": 0.0,
                "gate_compile_sec": 0.0,
                "ffn_compile_sec": 0.0,
                "load_cache_hit": True,
                "handle_cache_hit": True,
            }
            return self._block_cache[cache_key], (0.0, 0.0, 0.0), 0.0, True, cache_profile
        self._guard_memory(f"{axis}_layer{layer_index}_before_segment_compile", segment_index)
        before_hits = int(getattr(self.bridge, "load_cache_hits", 0))
        before_misses = int(getattr(self.bridge, "load_cache_misses", 0))
        started = time.perf_counter()
        handles, compile_times, compile_profiles = self._compile_axis_handles(
            axis,
            layer_index,
            batch,
            seq,
            valid_seq,
            fuse_residual=effective_fuse_residual,
        )
        compile_wall = time.perf_counter() - started
        after_hits = int(getattr(self.bridge, "load_cache_hits", 0))
        after_misses = int(getattr(self.bridge, "load_cache_misses", 0))
        self._guard_memory(f"{axis}_layer{layer_index}_after_segment_compile", segment_index)
        cached = False
        if cache_limit > 0 and segment_index < cache_limit:
            self._block_cache[cache_key] = handles
            cached = True
        cache_profile = {
            "load_or_compile_wall_sec": float(compile_wall),
            "compile_wall_sec": float(compile_wall),
            "pre_compile_sec": float(compile_times[0]),
            "gate_compile_sec": float(compile_times[1]),
            "ffn_compile_sec": float(compile_times[2]),
            "load_cache_hits_delta": int(after_hits - before_hits),
            "load_cache_misses_delta": int(after_misses - before_misses),
            "load_cache_hit": bool(after_hits > before_hits and after_misses == before_misses),
            "handle_cache_hit": False,
        }
        _accumulate_named_bridge_compile_profiles(cache_profile, compile_profiles)
        for name, profile in compile_profiles.items():
            route = profile.get("bridge_profile_route")
            if route:
                cache_profile[f"{name}_bridge_profile_route"] = str(route)
        return handles, compile_times, compile_wall, cached, cache_profile

    @staticmethod
    def _sum_profiles(profiles: list[dict[str, float]]) -> dict[str, float]:
        totals: dict[str, float] = {}
        for profile in profiles:
            for key, value in profile.items():
                totals[key] = totals.get(key, 0.0) + float(value)
        return totals

    def _run_block_profiled(
            self,
            handles,
            x_ane: np.ndarray,
            fuse_gate_ffn: bool = False,
            *,
            fuse_residual: bool | None = None,
    ) -> tuple[np.ndarray, dict[str, float]]:
        batch, _, _, seq = x_ane.shape
        fuse_residual = self._fuse_residual() if fuse_residual is None else bool(fuse_residual)
        two_input_gate = self._two_input_gate()
        bridge_pack_gate = self._bridge_pack_gate()
        surface_handoff_gate_ffn = bool(
            self._surface_handoff_gate_ffn() and fuse_residual and not fuse_gate_ffn
        )
        profile: dict[str, float] = {}
        profile["fuse_residual"] = 1.0 if fuse_residual else 0.0
        profile["fuse_gate_ffn"] = 1.0 if fuse_gate_ffn else 0.0
        profile["two_input_gate"] = 1.0 if two_input_gate else 0.0
        profile["bridge_pack_gate"] = 1.0 if bridge_pack_gate else 0.0
        profile["surface_handoff_gate_ffn"] = 1.0 if surface_handoff_gate_ffn else 0.0
        probe_scope = getattr(self.module, "private_ane_probe_transformer_handle_scope", None)

        if fuse_gate_ffn:
            pre, fused_handle = handles
            att_flat, pre_timing = self.bridge.run_profiled(pre, x_ane, (batch, INNER, 1, seq))
            for key, value in pre_timing.items():
                profile[f"ane_pre_{key}"] = float(value)

            pack_started = time.perf_counter()
            packed = np.empty((batch, DIM + INNER, 1, seq), dtype=np.float16)
            packed[:, :DIM] = x_ane
            packed[:, DIM:] = att_flat
            profile["att_pack_sec"] = float(time.perf_counter() - pack_started)
            out, fused_timing = self.bridge.run_profiled(fused_handle, packed, x_ane.shape)
            for key, value in fused_timing.items():
                profile[f"ane_fused_{key}"] = float(value)
            profile["ane_gate_total_sec"] = 0.0
            profile["ane_gate_eval_sec"] = 0.0
            profile["ane_ffn_total_sec"] = 0.0
            profile["ane_ffn_eval_sec"] = 0.0
            profile["att_residual_sec"] = 0.0
            profile["ffn_residual_sec"] = 0.0
            profile["ane_total_sec"] = float(pre_timing["total_sec"] + fused_timing["total_sec"])
            profile["ane_eval_only_sec"] = float(pre_timing["eval_sec"] + fused_timing["eval_sec"])
            profile["ane_write_sec"] = float(pre_timing["write_sec"] + fused_timing["write_sec"])
            profile["ane_read_sec"] = float(pre_timing["read_sec"] + fused_timing["read_sec"])
            return out, profile

        if len(handles) == 1:
            pre = handles[0]
            att_flat, pre_timing = self.bridge.run_profiled(pre, x_ane, (batch, INNER, 1, seq))
            for key, value in pre_timing.items():
                profile[f"ane_pre_{key}"] = float(value)
            profile["att_pack_sec"] = 0.0
            profile["ane_gate_total_sec"] = 0.0
            profile["ane_gate_eval_sec"] = 0.0
            profile["ane_ffn_total_sec"] = 0.0
            profile["ane_ffn_eval_sec"] = 0.0
            profile["att_residual_sec"] = 0.0
            profile["ffn_residual_sec"] = 0.0
            profile["ane_total_sec"] = float(pre_timing["total_sec"])
            profile["ane_eval_only_sec"] = float(pre_timing["eval_sec"])
            profile["ane_write_sec"] = float(pre_timing["write_sec"])
            profile["ane_read_sec"] = float(pre_timing["read_sec"])
            return x_ane, profile

        if len(handles) == 2:
            pre, gate = handles
            att_flat, pre_timing = self.bridge.run_profiled(pre, x_ane, (batch, INNER, 1, seq))
            for key, value in pre_timing.items():
                profile[f"ane_pre_{key}"] = float(value)
            if two_input_gate:
                profile["att_pack_sec"] = 0.0
                gate_outs, gate_timing = self.bridge.run_multi_inputs_profiled(gate, [x_ane, att_flat], [x_ane.shape])
                att_out = gate_outs[0]
            elif bridge_pack_gate:
                profile["att_pack_sec"] = 0.0
                att_out, gate_timing = self.bridge.run_packed2_profiled(gate, x_ane, att_flat, x_ane.shape)
            else:
                pack_started = time.perf_counter()
                packed = np.empty((batch, DIM + INNER, 1, seq), dtype=np.float16)
                packed[:, :DIM] = x_ane
                packed[:, DIM:] = att_flat
                profile["att_pack_sec"] = float(time.perf_counter() - pack_started)
                att_out, gate_timing = self.bridge.run_profiled(gate, packed, x_ane.shape)
            for key, value in gate_timing.items():
                profile[f"ane_gate_{key}"] = float(value)
            profile["ane_ffn_total_sec"] = 0.0
            profile["ane_ffn_eval_sec"] = 0.0
            profile["ffn_residual_sec"] = 0.0
            profile["ane_total_sec"] = float(pre_timing["total_sec"] + gate_timing["total_sec"])
            profile["ane_eval_only_sec"] = float(pre_timing["eval_sec"] + gate_timing["eval_sec"])
            profile["ane_write_sec"] = float(pre_timing["write_sec"] + gate_timing["write_sec"])
            profile["ane_read_sec"] = float(pre_timing["read_sec"] + gate_timing["read_sec"])
            return att_out, profile

        pre, gate, ffn_handle = handles

        att_flat, pre_timing = self.bridge.run_profiled(pre, x_ane, (batch, INNER, 1, seq))
        for key, value in pre_timing.items():
            profile[f"ane_pre_{key}"] = float(value)

        if surface_handoff_gate_ffn:
            if two_input_gate:
                write_started = time.perf_counter()
                self.bridge.write_input(gate, x_ane, 0)
                self.bridge.write_input(gate, att_flat, 1)
                gate_write_sec = time.perf_counter() - write_started
                gate_write_total_sec = gate_write_sec
                profile["att_pack_sec"] = 0.0
                gate_cast_sec = 0.0
            elif bridge_pack_gate:
                profile["att_pack_sec"] = 0.0
                write_timing = self.bridge.write_packed2_profiled(gate, x_ane, att_flat)
                gate_write_total_sec = float(write_timing["total_sec"])
                gate_write_sec = float(write_timing["write_sec"])
                gate_cast_sec = float(write_timing["cast_sec"])
            else:
                pack_started = time.perf_counter()
                packed = np.empty((batch, DIM + INNER, 1, seq), dtype=np.float16)
                packed[:, :DIM] = x_ane
                packed[:, DIM:] = att_flat
                profile["att_pack_sec"] = float(time.perf_counter() - pack_started)
                gate_write_sec = self.bridge.write_input(gate, packed)
                gate_write_total_sec = gate_write_sec
                gate_cast_sec = 0.0

            gate_eval_sec = self.bridge.eval(gate)
            gate_eval_profile = dict(getattr(self.bridge, "last_bridge_profile", {}) or {})
            bind_started = time.perf_counter()
            self.bridge.bind_input_to_output(ffn_handle, 0, gate, 0)
            profile["surface_handoff_bind_sec"] = float(time.perf_counter() - bind_started)
            ffn_eval_sec = self.bridge.eval(ffn_handle)
            ffn_eval_profile = dict(getattr(self.bridge, "last_bridge_profile", {}) or {})
            out, ffn_read_sec = self.bridge.read_output(ffn_handle, x_ane.shape)
            gate_timing = {
                "total_sec": float(gate_write_total_sec + gate_eval_sec),
                "cast_sec": float(gate_cast_sec),
                "alloc_sec": 0.0,
                "write_sec": float(gate_write_sec),
                "eval_sec": float(gate_eval_sec),
                "read_sec": 0.0,
            }
            ffn_timing = {
                "total_sec": float(ffn_eval_sec + ffn_read_sec),
                "cast_sec": 0.0,
                "alloc_sec": 0.0,
                "write_sec": 0.0,
                "eval_sec": float(ffn_eval_sec),
                "read_sec": float(ffn_read_sec),
            }
            for key, value in gate_timing.items():
                profile[f"ane_gate_{key}"] = float(value)
            for key, value in ffn_timing.items():
                profile[f"ane_ffn_{key}"] = float(value)
            _accumulate_named_bridge_compile_profiles(
                profile,
                {
                    "gate_eval": gate_eval_profile,
                    "ffn_eval": ffn_eval_profile,
                },
            )
            profile["att_residual_sec"] = 0.0
            profile["ffn_residual_sec"] = 0.0
            profile["ane_total_sec"] = float(
                pre_timing["total_sec"]
                + gate_timing["total_sec"]
                + profile["surface_handoff_bind_sec"]
                + ffn_timing["total_sec"]
            )
            profile["ane_eval_only_sec"] = float(
                pre_timing["eval_sec"] + gate_timing["eval_sec"] + ffn_timing["eval_sec"]
            )
            profile["ane_write_sec"] = float(pre_timing["write_sec"] + gate_timing["write_sec"])
            profile["ane_read_sec"] = float(pre_timing["read_sec"] + ffn_timing["read_sec"])
            return out, profile

        if two_input_gate:
            profile["att_pack_sec"] = 0.0
            gate_outs, gate_timing = self.bridge.run_multi_inputs_profiled(gate, [x_ane, att_flat], [x_ane.shape])
            att_out = gate_outs[0]
        elif bridge_pack_gate:
            profile["att_pack_sec"] = 0.0
            att_out, gate_timing = self.bridge.run_packed2_profiled(gate, x_ane, att_flat, x_ane.shape)
        else:
            pack_started = time.perf_counter()
            packed = np.empty((batch, DIM + INNER, 1, seq), dtype=np.float16)
            packed[:, :DIM] = x_ane
            packed[:, DIM:] = att_flat
            profile["att_pack_sec"] = float(time.perf_counter() - pack_started)
            att_out, gate_timing = self.bridge.run_profiled(gate, packed, x_ane.shape)
        for key, value in gate_timing.items():
            profile[f"ane_gate_{key}"] = float(value)

        if fuse_residual:
            x_ane = att_out
            profile["att_residual_sec"] = 0.0
        else:
            residual_started = time.perf_counter()
            x_ane = (x_ane.astype(np.float32) + att_out.astype(np.float32)).astype(np.float16, copy=False)
            np.nan_to_num(x_ane, copy=False, nan=0.0, posinf=65504.0, neginf=-65504.0)
            profile["att_residual_sec"] = float(time.perf_counter() - residual_started)

        ffn_out, ffn_timing = self.bridge.run_profiled(ffn_handle, x_ane, x_ane.shape)
        for key, value in ffn_timing.items():
            profile[f"ane_ffn_{key}"] = float(value)

        if fuse_residual:
            out = ffn_out
            profile["ffn_residual_sec"] = 0.0
        else:
            residual_started = time.perf_counter()
            out = (x_ane.astype(np.float32) + ffn_out.astype(np.float32)).astype(np.float16, copy=False)
            np.nan_to_num(out, copy=False, nan=0.0, posinf=65504.0, neginf=-65504.0)
            profile["ffn_residual_sec"] = float(time.perf_counter() - residual_started)

        profile["ane_total_sec"] = float(
            pre_timing["total_sec"] + gate_timing["total_sec"] + ffn_timing["total_sec"]
        )
        profile["ane_eval_only_sec"] = float(
            pre_timing["eval_sec"] + gate_timing["eval_sec"] + ffn_timing["eval_sec"]
        )
        profile["ane_write_sec"] = float(
            pre_timing["write_sec"] + gate_timing["write_sec"] + ffn_timing["write_sec"]
        )
        profile["ane_read_sec"] = float(
            pre_timing["read_sec"] + gate_timing["read_sec"] + ffn_timing["read_sec"]
        )
        return out, profile

    def _run_time_axis_with_handles(self, handles, x: np.ndarray, scratch: np.ndarray | None = None):
        pack_started = time.perf_counter()
        b, t, f, d = x.shape
        padded_shape = (b * f, d, 1, TIME_PAD)
        reused_scratch = scratch is not None and scratch.shape == padded_shape
        if not reused_scratch:
            scratch = np.empty(padded_shape, dtype=np.float16)
        padded = scratch
        padded_view = padded.reshape(b, f, d, 1, TIME_PAD)
        padded_view[..., 0, :t] = x.transpose(0, 2, 3, 1)
        if t < TIME_PAD:
            padded_view[..., 0, t:] = 0
        pack_sec = time.perf_counter() - pack_started
        out, profile = self._run_block_profiled(handles, padded, self._fuse_gate_ffn_axis("time", padded.shape[0], TIME_PAD))
        unpack_started = time.perf_counter()
        out = out[..., :t].reshape(b, f, d, t)
        result = out.transpose(0, 3, 1, 2).astype(np.float16, copy=False)
        profile["axis_pack_sec"] = float(pack_sec)
        profile["axis_pack_reused"] = 1.0 if reused_scratch else 0.0
        profile["axis_unpack_sec"] = float(time.perf_counter() - unpack_started)
        return result, profile, scratch

    def _run_time_axis_direct_freq_with_handles(
            self,
            handles,
            x: np.ndarray,
            scratch: np.ndarray | None = None,
            *,
            unpadded: bool = False,
    ):
        pack_started = time.perf_counter()
        b, t, f, d = x.shape
        padded_shape = (b * f, d, 1, TIME_PAD)
        reused_scratch = scratch is not None and scratch.shape == padded_shape
        if not reused_scratch:
            scratch = np.empty(padded_shape, dtype=np.float16)
        padded = scratch
        padded_view = padded.reshape(b, f, d, 1, TIME_PAD)
        padded_view[..., 0, :t] = x.transpose(0, 2, 3, 1)
        if t < TIME_PAD:
            padded_view[..., 0, t:] = 0
        pack_sec = time.perf_counter() - pack_started
        out, profile = self._run_block_profiled(
            handles,
            padded,
            self._fuse_gate_ffn_axis("time", padded.shape[0], TIME_PAD),
        )
        repack_started = time.perf_counter()
        # The unpadded freq MIL compiles with seq=62, but the ANE eval surface
        # contract still requires FREQ_PAD-sized input/output byte strides.
        freq_seq = FREQ_PAD
        freq_padded = np.empty((b * t, d, 1, freq_seq), dtype=np.float16)
        freq_view = out[..., :t].reshape(b, f, d, t).transpose(0, 3, 2, 1).reshape(b * t, d, 1, f)
        freq_padded[..., :f] = freq_view
        if f < freq_seq:
            freq_padded[..., f:] = 0
        repack_sec = time.perf_counter() - repack_started
        profile["axis_pack_sec"] = float(pack_sec + repack_sec)
        profile["axis_pack_reused"] = 1.0 if reused_scratch else 0.0
        profile["axis_unpack_sec"] = 0.0
        profile["direct_time_to_freq_repack"] = 1.0
        profile["direct_time_to_freq_unpadded"] = 1.0 if unpadded else 0.0
        profile["direct_time_to_freq_repack_sec"] = float(repack_sec)
        return freq_padded, (b, t, f, d), profile, scratch

    def _run_freq_axis_with_handles(self, handles, x: np.ndarray, scratch: np.ndarray | None = None):
        pack_started = time.perf_counter()
        b, t, f, d = x.shape
        x_ane = x.transpose(0, 1, 3, 2).reshape(b * t, d, 1, f)
        padded_shape = (b * t, d, 1, FREQ_PAD)
        reused_scratch = scratch is not None and scratch.shape == padded_shape
        if not reused_scratch:
            scratch = np.empty(padded_shape, dtype=np.float16)
        padded = scratch
        padded[..., :f] = x_ane
        if f < FREQ_PAD:
            padded[..., f:] = 0
        pack_sec = time.perf_counter() - pack_started
        out, profile = self._run_block_profiled(handles, padded, self._fuse_gate_ffn_axis("freq", padded.shape[0], FREQ_PAD))
        unpack_started = time.perf_counter()
        out = out[..., :f].reshape(b, t, d, f)
        result = out.transpose(0, 1, 3, 2).astype(np.float16, copy=False)
        profile["axis_pack_sec"] = float(pack_sec)
        profile["axis_pack_reused"] = 1.0 if reused_scratch else 0.0
        profile["axis_unpack_sec"] = float(time.perf_counter() - unpack_started)
        return result, profile, scratch

    def _run_freq_axis_packed_with_handles(
            self,
            handles,
            padded: np.ndarray,
            shape: tuple[int, int, int, int],
            *,
            unpadded: bool = False,
    ):
        b, t, f, d = shape
        seq = int(padded.shape[3])
        out, profile = self._run_block_profiled(
            handles,
            padded,
            self._fuse_gate_ffn_axis("freq", padded.shape[0], seq),
        )
        unpack_started = time.perf_counter()
        out = out[..., :f].reshape(b, t, d, f)
        result = out.transpose(0, 1, 3, 2).astype(np.float16, copy=False)
        profile["axis_pack_sec"] = 0.0
        profile["axis_pack_reused"] = 1.0
        profile["axis_unpack_sec"] = float(time.perf_counter() - unpack_started)
        profile["direct_time_to_freq_repack_consumed"] = 1.0
        profile["direct_time_to_freq_unpadded_consumed"] = 1.0 if unpadded else 0.0
        return result, profile

    def _run_time_axis_many_with_handles(
            self,
            handles,
            xs: list[np.ndarray],
            *,
            fuse_residual: bool | None = None,
    ):
        pack_started = time.perf_counter()
        x = np.concatenate(xs, axis=0)
        b, t, f, d = x.shape
        x_ane = x.transpose(0, 2, 3, 1).reshape(b * f, d, 1, t)
        padded = np.empty((b * f, d, 1, TIME_PAD), dtype=np.float16)
        padded[..., :t] = x_ane
        if t < TIME_PAD:
            padded[..., t:] = 0
        pack_sec = time.perf_counter() - pack_started
        out, profile = self._run_block_profiled(
            handles,
            padded,
            self._fuse_gate_ffn_axis("time", padded.shape[0], TIME_PAD),
            fuse_residual=fuse_residual,
        )
        unpack_started = time.perf_counter()
        out = out[..., :t].reshape(b, f, d, t)
        result = out.transpose(0, 3, 1, 2).astype(np.float16, copy=False)
        profile["axis_pack_sec"] = float(pack_sec)
        profile["axis_pack_reused"] = float(max(0, b - 1))
        profile["axis_unpack_sec"] = float(time.perf_counter() - unpack_started)
        return [np.ascontiguousarray(result[index:index + 1], dtype=np.float16) for index in range(b)], profile

    def _run_freq_axis_many_with_handles(
            self,
            handles,
            xs: list[np.ndarray],
            *,
            fuse_residual: bool | None = None,
    ):
        pack_started = time.perf_counter()
        x = np.concatenate(xs, axis=0)
        b, t, f, d = x.shape
        padded = np.empty((b * t, d, 1, FREQ_PAD), dtype=np.float16)
        x_ane = x.transpose(0, 1, 3, 2).reshape(b * t, d, 1, f)
        padded[..., :f] = x_ane
        if f < FREQ_PAD:
            padded[..., f:] = 0
        pack_sec = time.perf_counter() - pack_started
        out, profile = self._run_block_profiled(
            handles,
            padded,
            self._fuse_gate_ffn_axis("freq", padded.shape[0], FREQ_PAD),
            fuse_residual=fuse_residual,
        )
        unpack_started = time.perf_counter()
        out = out[..., :f].reshape(b, t, d, f)
        result = out.transpose(0, 1, 3, 2).astype(np.float16, copy=False)
        profile["axis_pack_sec"] = float(pack_sec)
        profile["axis_pack_reused"] = float(max(0, b - 1))
        profile["axis_unpack_sec"] = float(time.perf_counter() - unpack_started)
        return [np.ascontiguousarray(result[index:index + 1], dtype=np.float16) for index in range(b)], profile

    def run_transformers_layerwise_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        wall_started = time.perf_counter()
        contiguous_started = time.perf_counter()
        xs = [np.ascontiguousarray(x, dtype=np.float16) for x in xs]
        input_contiguous_sec = time.perf_counter() - contiguous_started
        timings = []
        transformer_detail = {
            "input_contiguous_sec": float(input_contiguous_sec),
            "start_guard_sec": 0.0,
            "post_eval_gc_sec": 0.0,
            "post_eval_guard_sec": 0.0,
            "post_free_guard_sec": 0.0,
            "timing_bookkeeping_sec": 0.0,
            "post_eval_gc_runs": 0,
            "post_eval_guard_runs": 0,
            "post_free_guard_runs": 0,
            "hot_gc_interval": int(self._transformer_hot_gc_interval()),
            "guard_interval": int(self._transformer_guard_interval()),
        }
        self.last_memory_samples = []
        guard_started = time.perf_counter()
        self._guard_memory("transformers_start")
        transformer_detail["start_guard_sec"] = float(time.perf_counter() - guard_started)
        if self._skip_transformers():
            self.last_timings = timings
            transformer_detail["wall_sec"] = float(time.perf_counter() - wall_started)
            transformer_detail["segments"] = 0
            self.last_transformer_detail_timing = transformer_detail
            return xs
        segment_index = 0
        batch_axis_requested = self._batch_axis_eval() and len(xs) > 1
        segment_known_keys = (
            "load_or_compile_wall_sec",
            "eval_sec",
            "handle_free_sec",
            "gc_sec",
            "post_eval_gc_sec",
            "post_eval_guard_sec",
            "post_free_guard_sec",
            "timing_bookkeeping_sec",
        )
        for layer_index in range(self._max_transformer_layers()):
            handles = None
            cached = False
            timing = None
            segment_wall_started = time.perf_counter()
            try:
                scope = getattr(self.module, "private_ane_probe_transformer_handle_scope", "full")
                time_axis_batch = len(xs) * FREQ_SEQ
                time_batch_axis_eval = (
                    batch_axis_requested
                    and self._batch_axis_attention_pre_supported("time", time_axis_batch, TIME_PAD)
                )
                stop_after_layer = int(getattr(self.module, "private_ane_probe_stop_after_transformer_layer", 0) or 0)
                stop_after_axis = getattr(self.module, "private_ane_probe_stop_after_transformer_axis", None)
                direct_time_to_freq = (
                    (self._direct_time_to_freq_repack() or self._direct_time_to_freq_unpadded())
                    and not time_batch_axis_eval
                    and not (
                        stop_after_axis == "time"
                        and stop_after_layer > 0
                        and (layer_index + 1) >= stop_after_layer
                    )
                )
                direct_freq_inputs = None
                time_fuse_residual = self._fuse_residual() and not time_batch_axis_eval
                axis_batch = time_axis_batch if time_batch_axis_eval else FREQ_SEQ
                handles, compile_times, compile_wall, cached, handle_profile = self._compile_axis_handles_cached(
                    "time",
                    layer_index,
                    segment_index,
                    axis_batch,
                    TIME_PAD,
                    TIME_SEQ,
                    fuse_residual=time_fuse_residual,
                )
                if scope in ("pre", "pre_gate"):
                    stop_after_layer = int(getattr(self.module, "private_ane_probe_stop_after_transformer_layer", 0) or 0)
                    stop_after_axis = getattr(self.module, "private_ane_probe_stop_after_transformer_axis", None)
                    if stop_after_axis == "time" and stop_after_layer > 0 and (layer_index + 1) >= stop_after_layer:
                        if scope == "pre":
                            handles = handles[:1]
                        elif scope == "pre_gate":
                            handles = handles[:2]
                eval_started = time.perf_counter()
                eval_profile: dict[str, float] = {}
                if time_batch_axis_eval:
                    xs, profile = self._run_time_axis_many_with_handles(
                        handles,
                        xs,
                        fuse_residual=time_fuse_residual,
                    )
                    for key, value in profile.items():
                        eval_profile[key] = eval_profile.get(key, 0.0) + float(value)
                    del profile
                else:
                    axis_scratch = None
                    if direct_time_to_freq:
                        direct_freq_inputs = []
                        for index, x in enumerate(xs):
                            freq_padded, freq_shape, profile, axis_scratch = self._run_time_axis_direct_freq_with_handles(
                                handles,
                                x,
                                axis_scratch,
                                unpadded=self._direct_time_to_freq_unpadded(),
                            )
                            direct_freq_inputs.append((freq_padded, freq_shape))
                            xs[index] = None
                            del x, freq_padded, freq_shape
                            for key, value in profile.items():
                                eval_profile[key] = eval_profile.get(key, 0.0) + float(value)
                            del profile
                    else:
                        for index, x in enumerate(xs):
                            y, profile, axis_scratch = self._run_time_axis_with_handles(handles, x, axis_scratch)
                            xs[index] = y
                            del x, y
                            for key, value in profile.items():
                                eval_profile[key] = eval_profile.get(key, 0.0) + float(value)
                            del profile
                    del axis_scratch
                eval_sec = time.perf_counter() - eval_started
                post_eval_gc_sec, post_eval_gc_ran = self._profile_hot_transformer_gc(segment_index)
                post_eval_guard_sec, post_eval_guard_ran = self._profile_transformer_guard(
                    f"time_layer{layer_index}_after_eval",
                    segment_index,
                )
                transformer_detail["post_eval_gc_sec"] += float(post_eval_gc_sec)
                transformer_detail["post_eval_guard_sec"] += float(post_eval_guard_sec)
                transformer_detail["post_eval_gc_runs"] += int(post_eval_gc_ran)
                transformer_detail["post_eval_guard_runs"] += int(post_eval_guard_ran)
                bookkeeping_started = time.perf_counter()
                timing = {
                    "axis": "time",
                    "layer": layer_index,
                    "pre_compile_sec": float(compile_times[0]),
                    "gate_compile_sec": float(compile_times[1]),
                    "ffn_compile_sec": float(compile_times[2]),
                    "load_or_compile_wall_sec": float(
                        handle_profile.get("load_or_compile_wall_sec", compile_wall)
                    ),
                    "load_cache_hits_delta": int(handle_profile.get("load_cache_hits_delta", 0) or 0),
                    "load_cache_misses_delta": int(handle_profile.get("load_cache_misses_delta", 0) or 0),
                    "load_cache_hit": bool(handle_profile.get("load_cache_hit", False)),
                    "handle_cache_hit": bool(handle_profile.get("handle_cache_hit", False)),
                    "fuse_residual": bool(time_fuse_residual),
                    "fuse_gate_ffn": bool(self._fuse_gate_ffn()),
                    "batch_axis_requested": bool(batch_axis_requested),
                    "batch_axis_supported": bool(time_batch_axis_eval),
                    "batch_axis_eval": bool(time_batch_axis_eval),
                    "tiled_time_attention_pre": bool(
                        self._tiled_attention_pre_for_shape(
                            "time",
                            layer_index,
                            axis_batch,
                            TIME_PAD,
                            TIME_SEQ,
                        )
                    ),
                    "tiled_time_attention_pre_q_chunk": (
                        self._tiled_time_attention_pre_q_chunk()
                        if self._tiled_attention_pre_for_shape(
                            "time",
                            layer_index,
                            axis_batch,
                            TIME_PAD,
                            TIME_SEQ,
                        ) else 0
                    ),
                    "compile_wall_sec": float(compile_wall),
                    "eval_sec": float(eval_sec),
                    "cache_hit": bool(compile_wall == 0.0),
                    "cache_kept": bool(cached),
                    "post_eval_gc_sec": float(post_eval_gc_sec),
                    "post_eval_gc_ran": bool(post_eval_gc_ran),
                    "post_eval_guard_sec": float(post_eval_guard_sec),
                    "post_eval_guard_ran": bool(post_eval_guard_ran),
                }
                _accumulate_bridge_profile_totals(transformer_detail, handle_profile)
                timing.update(eval_profile)
                for key, value in handle_profile.items():
                    if key.startswith("bridge_profile_") or "_bridge_profile_" in key:
                        timing[key] = value
                timing["timing_bookkeeping_sec"] = float(time.perf_counter() - bookkeeping_started)
                transformer_detail["timing_bookkeeping_sec"] += float(timing["timing_bookkeeping_sec"])
                timings.append(timing)
            finally:
                handle_free_sec = 0.0
                gc_sec = 0.0
                post_free_guard_sec = 0.0
                post_free_guard_ran = False
                if handles is not None and not cached:
                    handle_free_sec, gc_sec = self._profile_free_handles(handles, family="transformer_time")
                else:
                    gc_sec = self._profile_gc()
                post_free_guard_sec, post_free_guard_ran = self._profile_transformer_guard(
                    f"time_layer{layer_index}_after_free",
                    segment_index,
                )
                transformer_detail["post_free_guard_sec"] += float(post_free_guard_sec)
                transformer_detail["post_free_guard_runs"] += int(post_free_guard_ran)
                if timing is not None:
                    timing["handle_free_sec"] = float(handle_free_sec)
                    timing["gc_sec"] = float(gc_sec)
                    timing["post_free_guard_sec"] = float(post_free_guard_sec)
                    timing["post_free_guard_ran"] = bool(post_free_guard_ran)
                    segment_wall_sec = float(time.perf_counter() - segment_wall_started)
                    segment_known_sec = sum(float(timing.get(key, 0.0) or 0.0) for key in segment_known_keys)
                    timing["segment_wall_sec"] = segment_wall_sec
                    timing["segment_known_sec"] = float(segment_known_sec)
                    timing["segment_outer_gap_sec"] = max(0.0, segment_wall_sec - float(segment_known_sec))
            segment_index += 1
            stop_after_layer = int(getattr(self.module, "private_ane_probe_stop_after_transformer_layer", 0) or 0)
            stop_after_axis = getattr(self.module, "private_ane_probe_stop_after_transformer_axis", None)
            if stop_after_layer > 0 and stop_after_axis == "time" and (layer_index + 1) >= stop_after_layer:
                self.last_timings = timings
                transformer_detail["wall_sec"] = float(time.perf_counter() - wall_started)
                transformer_detail["segments"] = int(segment_index)
                self.last_transformer_detail_timing = transformer_detail
                return xs

            handles = None
            cached = False
            timing = None
            segment_wall_started = time.perf_counter()
            try:
                freq_axis_batch = len(xs) * TIME_SEQ
                freq_seq = (
                    FREQ_SEQ
                    if direct_freq_inputs is not None and self._direct_time_to_freq_unpadded()
                    else FREQ_PAD
                )
                freq_batch_axis_eval = (
                    batch_axis_requested
                    and self._batch_axis_attention_pre_supported("freq", freq_axis_batch, freq_seq)
                )
                freq_fuse_residual = self._fuse_residual() and not freq_batch_axis_eval
                axis_batch = freq_axis_batch if freq_batch_axis_eval else TIME_SEQ
                handles, compile_times, compile_wall, cached, handle_profile = self._compile_axis_handles_cached(
                    "freq",
                    layer_index,
                    segment_index,
                    axis_batch,
                    freq_seq,
                    FREQ_SEQ,
                    fuse_residual=freq_fuse_residual,
                )
                eval_started = time.perf_counter()
                eval_profile: dict[str, float] = {}
                if freq_batch_axis_eval:
                    xs, profile = self._run_freq_axis_many_with_handles(
                        handles,
                        xs,
                        fuse_residual=freq_fuse_residual,
                    )
                    for key, value in profile.items():
                        eval_profile[key] = eval_profile.get(key, 0.0) + float(value)
                    del profile
                else:
                    axis_scratch = None
                    if direct_freq_inputs is not None:
                        for index, (freq_padded, freq_shape) in enumerate(direct_freq_inputs):
                            y, profile = self._run_freq_axis_packed_with_handles(
                                handles,
                                freq_padded,
                                freq_shape,
                                unpadded=self._direct_time_to_freq_unpadded(),
                            )
                            xs[index] = y
                            del freq_padded, freq_shape, y
                            for key, value in profile.items():
                                eval_profile[key] = eval_profile.get(key, 0.0) + float(value)
                            del profile
                        direct_freq_inputs = None
                    else:
                        for index, x in enumerate(xs):
                            y, profile, axis_scratch = self._run_freq_axis_with_handles(handles, x, axis_scratch)
                            xs[index] = y
                            del x, y
                            for key, value in profile.items():
                                eval_profile[key] = eval_profile.get(key, 0.0) + float(value)
                            del profile
                    del axis_scratch
                eval_sec = time.perf_counter() - eval_started
                post_eval_gc_sec, post_eval_gc_ran = self._profile_hot_transformer_gc(segment_index)
                post_eval_guard_sec, post_eval_guard_ran = self._profile_transformer_guard(
                    f"freq_layer{layer_index}_after_eval",
                    segment_index,
                )
                transformer_detail["post_eval_gc_sec"] += float(post_eval_gc_sec)
                transformer_detail["post_eval_guard_sec"] += float(post_eval_guard_sec)
                transformer_detail["post_eval_gc_runs"] += int(post_eval_gc_ran)
                transformer_detail["post_eval_guard_runs"] += int(post_eval_guard_ran)
                bookkeeping_started = time.perf_counter()
                timing = {
                    "axis": "freq",
                    "layer": layer_index,
                    "pre_compile_sec": float(compile_times[0]),
                    "gate_compile_sec": float(compile_times[1]),
                    "ffn_compile_sec": float(compile_times[2]),
                    "load_or_compile_wall_sec": float(
                        handle_profile.get("load_or_compile_wall_sec", compile_wall)
                    ),
                    "load_cache_hits_delta": int(handle_profile.get("load_cache_hits_delta", 0) or 0),
                    "load_cache_misses_delta": int(handle_profile.get("load_cache_misses_delta", 0) or 0),
                    "load_cache_hit": bool(handle_profile.get("load_cache_hit", False)),
                    "handle_cache_hit": bool(handle_profile.get("handle_cache_hit", False)),
                    "fuse_residual": bool(freq_fuse_residual),
                    "fuse_gate_ffn": bool(self._fuse_gate_ffn()),
                    "batch_axis_requested": bool(batch_axis_requested),
                    "batch_axis_supported": bool(freq_batch_axis_eval),
                    "batch_axis_eval": bool(freq_batch_axis_eval),
                    "tiled_time_attention_pre": bool(
                        self._tiled_attention_pre_for_shape(
                            "freq",
                            layer_index,
                            freq_axis_batch,
                            FREQ_PAD,
                            freq_seq,
                        )
                    ),
                    "tiled_time_attention_pre_q_chunk": (
                        self._tiled_time_attention_pre_q_chunk()
                        if self._tiled_attention_pre_for_shape(
                            "freq",
                            layer_index,
                            freq_axis_batch,
                            FREQ_PAD,
                            freq_seq,
                        ) else 0
                    ),
                    "compile_wall_sec": float(compile_wall),
                    "eval_sec": float(eval_sec),
                    "cache_hit": bool(compile_wall == 0.0),
                    "cache_kept": bool(cached),
                    "post_eval_gc_sec": float(post_eval_gc_sec),
                    "post_eval_gc_ran": bool(post_eval_gc_ran),
                    "post_eval_guard_sec": float(post_eval_guard_sec),
                    "post_eval_guard_ran": bool(post_eval_guard_ran),
                }
                _accumulate_bridge_profile_totals(transformer_detail, handle_profile)
                timing.update(eval_profile)
                for key, value in handle_profile.items():
                    if key.startswith("bridge_profile_") or "_bridge_profile_" in key:
                        timing[key] = value
                timing["timing_bookkeeping_sec"] = float(time.perf_counter() - bookkeeping_started)
                transformer_detail["timing_bookkeeping_sec"] += float(timing["timing_bookkeeping_sec"])
                timings.append(timing)
            finally:
                handle_free_sec = 0.0
                gc_sec = 0.0
                post_free_guard_sec = 0.0
                post_free_guard_ran = False
                if handles is not None and not cached:
                    handle_free_sec, gc_sec = self._profile_free_handles(handles, family="transformer_freq")
                else:
                    gc_sec = self._profile_gc()
                post_free_guard_sec, post_free_guard_ran = self._profile_transformer_guard(
                    f"freq_layer{layer_index}_after_free",
                    segment_index,
                )
                transformer_detail["post_free_guard_sec"] += float(post_free_guard_sec)
                transformer_detail["post_free_guard_runs"] += int(post_free_guard_ran)
                if timing is not None:
                    timing["handle_free_sec"] = float(handle_free_sec)
                    timing["gc_sec"] = float(gc_sec)
                    timing["post_free_guard_sec"] = float(post_free_guard_sec)
                    timing["post_free_guard_ran"] = bool(post_free_guard_ran)
                    segment_wall_sec = float(time.perf_counter() - segment_wall_started)
                    segment_known_sec = sum(float(timing.get(key, 0.0) or 0.0) for key in segment_known_keys)
                    timing["segment_wall_sec"] = segment_wall_sec
                    timing["segment_known_sec"] = float(segment_known_sec)
                    timing["segment_outer_gap_sec"] = max(0.0, segment_wall_sec - float(segment_known_sec))
            segment_index += 1
            stop_after_layer = int(getattr(self.module, "private_ane_probe_stop_after_transformer_layer", 0) or 0)
            stop_after_axis = getattr(self.module, "private_ane_probe_stop_after_transformer_axis", None)
            if stop_after_layer > 0 and stop_after_axis == "freq" and (layer_index + 1) >= stop_after_layer:
                self.last_timings = timings
                transformer_detail["wall_sec"] = float(time.perf_counter() - wall_started)
                transformer_detail["segments"] = int(segment_index)
                self.last_transformer_detail_timing = transformer_detail
                return xs
        self.last_timings = timings
        transformer_detail["wall_sec"] = float(time.perf_counter() - wall_started)
        transformer_detail["segments"] = int(segment_index)
        self.last_transformer_detail_timing = transformer_detail
        return xs

    def _run_time_axis(self, layer_index: int, x: np.ndarray):
        b, t, f, d = x.shape
        padded = np.empty((b * f, d, 1, TIME_PAD), dtype=np.float16)
        padded_view = padded.reshape(b, f, d, 1, TIME_PAD)
        padded_view[..., 0, :t] = x.transpose(0, 2, 3, 1)
        if t < TIME_PAD:
            padded_view[..., 0, t:] = 0
        out, compile_times, eval_sec = self._compile_run_free_axis("time", layer_index, padded, TIME_PAD, TIME_SEQ)
        del padded
        out = out[..., :t].reshape(b, f, d, t)
        return out.transpose(0, 3, 1, 2).astype(np.float16, copy=False), compile_times, eval_sec

    def _run_freq_axis(self, layer_index: int, x: np.ndarray):
        b, t, f, d = x.shape
        x_ane = x.transpose(0, 1, 3, 2).reshape(b * t, d, 1, f)
        padded = np.empty((b * t, d, 1, FREQ_PAD), dtype=np.float16)
        padded[..., :f] = x_ane
        if f < FREQ_PAD:
            padded[..., f:] = 0
        del x_ane
        out, compile_times, eval_sec = self._compile_run_free_axis("freq", layer_index, padded, FREQ_PAD, FREQ_SEQ)
        del padded
        out = out[..., :f].reshape(b, t, d, f)
        return out.transpose(0, 1, 3, 2).astype(np.float16, copy=False), compile_times, eval_sec

    def run_transformers(self, x: np.ndarray) -> np.ndarray:
        self._validate_shape(x)
        x = np.ascontiguousarray(x, dtype=np.float16)
        timings = []
        self.last_memory_samples = []
        self._guard_memory("transformers_start")
        if self._skip_transformers():
            self.last_timings = timings
            return x
        for layer_index in range(self._max_transformer_layers()):
            x, compile_times, eval_sec = self._run_time_axis(layer_index, x)
            x32 = x.astype(np.float32)
            timings.append({
                "axis": "time",
                "layer": layer_index,
                "pre_compile_sec": float(compile_times[0]),
                "gate_compile_sec": float(compile_times[1]),
                "ffn_compile_sec": float(compile_times[2]),
                "fuse_gate_ffn": bool(self._fuse_gate_ffn()),
                "tiled_time_attention_pre": bool(self._tiled_attention_pre_axis("time", layer_index)),
                "tiled_time_attention_pre_q_chunk": (
                    self._tiled_time_attention_pre_q_chunk()
                    if self._tiled_attention_pre_axis("time", layer_index) else 0
                ),
                "eval_sec": float(eval_sec),
                "abs_max": float(np.nanmax(np.abs(x32))),
                "rms": float(np.sqrt(np.nanmean(x32 * x32))),
                "nonfinite": int(np.size(x) - np.isfinite(x32).sum()),
            })
            x, compile_times, eval_sec = self._run_freq_axis(layer_index, x)
            x32 = x.astype(np.float32)
            timings.append({
                "axis": "freq",
                "layer": layer_index,
                "pre_compile_sec": float(compile_times[0]),
                "gate_compile_sec": float(compile_times[1]),
                "ffn_compile_sec": float(compile_times[2]),
                "fuse_gate_ffn": bool(self._fuse_gate_ffn()),
                "tiled_time_attention_pre": bool(self._tiled_attention_pre_axis("freq", layer_index)),
                "tiled_time_attention_pre_q_chunk": (
                    self._tiled_time_attention_pre_q_chunk()
                    if self._tiled_attention_pre_axis("freq", layer_index) else 0
                ),
                "eval_sec": float(eval_sec),
                "abs_max": float(np.nanmax(np.abs(x32))),
                "rms": float(np.sqrt(np.nanmean(x32 * x32))),
                "nonfinite": int(np.size(x) - np.isfinite(x32).sum()),
            })
        self.last_timings = timings
        return x

    def run_band_split(self, x: np.ndarray) -> np.ndarray:
        x = np.ascontiguousarray(x, dtype=np.float16)
        if x.shape != (1, INPUT_DIM, 1, TIME_SEQ):
            raise ValueError(f"private_ane band split expects (1,{INPUT_DIM},1,{TIME_SEQ}), got {x.shape}")
        out = np.empty((1, TIME_SEQ, BAND_COUNT, DIM), dtype=np.float16)
        total_compile = 0.0
        total_eval = 0.0
        offset = 0
        for band_index, (dim_in, to_feature) in enumerate(zip(self.module.band_split.dim_inputs, self.module.band_split.to_features, strict=True)):
            band_x = np.ascontiguousarray(x[:, offset:offset + dim_in], dtype=np.float16)
            offset += dim_in
            started = time.perf_counter()
            handle = self._compile_bridge(
                f"band_split_full_{band_index}",
                _band_feature_mil(dim_in, TIME_SEQ),
                _band_feature_weights(to_feature),
                band_x.nbytes,
                DIM * TIME_SEQ * 2,
            )
            compile_sec = time.perf_counter() - started
            try:
                eval_started = time.perf_counter()
                band = self.bridge.run(handle, band_x, (1, DIM, 1, TIME_SEQ))
                eval_sec = time.perf_counter() - eval_started
            finally:
                self.bridge.free(handle)
                gc.collect()
            total_compile += compile_sec
            total_eval += eval_sec
            out[:, :, band_index, :] = band.reshape(1, DIM, TIME_SEQ).transpose(0, 2, 1)
        self.last_band_split_timing = {"compile_sec": float(total_compile), "eval_sec": float(total_eval)}
        return out

    def run_band_split_tiled(self, x: np.ndarray) -> np.ndarray:
        x = np.ascontiguousarray(x, dtype=np.float32)
        if x.shape != (1, INPUT_DIM, 1, TIME_SEQ):
            raise ValueError(f"private_ane band split expects (1,{INPUT_DIM},1,{TIME_SEQ}), got {x.shape}")
        out = np.empty((1, TIME_SEQ, BAND_COUNT, DIM), dtype=np.float16)
        total_compile = 0.0
        total_eval = 0.0
        offset = 0
        for band_index, (dim_in, to_feature) in enumerate(zip(self.module.band_split.dim_inputs, self.module.band_split.to_features, strict=True)):
            started = time.perf_counter()
            handle = self._compile_bridge(
                f"band_split_tile_{band_index}",
                _band_feature_tile_mil(dim_in, TILE_SEQ),
                _band_feature_weights(to_feature),
                dim_in * TILE_SEQ * 2,
                DIM * TILE_SEQ * 2,
            )
            total_compile += time.perf_counter() - started
            try:
                for tile_start in range(0, TIME_SEQ, TILE_SEQ):
                    tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
                    valid = tile_end - tile_start
                    tile = np.zeros((1, dim_in, 1, TILE_SEQ), dtype=np.float16)
                    tile_src = x[:, offset:offset + dim_in, :, tile_start:tile_end]
                    tile_abs_max = float(np.max(np.abs(tile_src)))
                    tile_scale = max(1.0, tile_abs_max / BAND_INPUT_TARGET_MAX)
                    tile[..., :valid] = (tile_src / np.float32(tile_scale)).astype(np.float16)
                    eval_started = time.perf_counter()
                    band = self.bridge.run(handle, tile, (1, DIM, 1, TILE_SEQ))
                    total_eval += time.perf_counter() - eval_started
                    out[:, tile_start:tile_end, band_index, :] = band[..., :valid].reshape(1, DIM, valid).transpose(0, 2, 1)
            finally:
                self.bridge.free(handle)
                gc.collect()
            offset += dim_in
        self.last_band_split_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "tile_seq": TILE_SEQ,
            "input_target_max": BAND_INPUT_TARGET_MAX,
        }
        return out

    def run_band_split_l2norm_prescaled(self, x: np.ndarray) -> np.ndarray:
        return self.run_band_split_l2norm_prescaled_many([x])[0]

    def run_band_split_l2norm(self, x: np.ndarray) -> np.ndarray:
        return self.run_band_split_l2norm_many([x])[0]

    def run_band_split_l2norm_fused(self, x: np.ndarray) -> np.ndarray:
        return self.run_band_split_l2norm_fused_many([x])[0]

    def run_band_split_l2norm_fused_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        wall_started = time.perf_counter()
        xs = [np.ascontiguousarray(x, dtype=np.float32) for x in xs]
        for x in xs:
            if x.shape != (1, INPUT_DIM, 1, TIME_SEQ):
                raise ValueError(f"private_ane band split expects (1,{INPUT_DIM},1,{TIME_SEQ}), got {x.shape}")
        if not xs:
            return []
        dim_inputs = tuple(int(dim) for dim in self.module.band_split.dim_inputs)
        if len(dim_inputs) != BAND_COUNT or sum(dim_inputs) != INPUT_DIM:
            raise ValueError(
                f"private_ane fused band split expects {BAND_COUNT} bands summing to {INPUT_DIM}, "
                f"got {len(dim_inputs)} bands summing to {sum(dim_inputs)}"
            )
        dim_offsets = getattr(self.module.band_split, "_dim_offsets", None)
        if dim_offsets is None:
            dim_offsets = (0, *np.cumsum(np.array(dim_inputs, dtype=np.int64)).tolist())
        dim_groups = getattr(self.module.band_split, "_dim_groups", None)
        if dim_groups is None:
            dim_groups = []
            start = 0
            for index in range(1, len(dim_inputs) + 1):
                if index == len(dim_inputs) or dim_inputs[index] != dim_inputs[start]:
                    dim_groups.append((start, index, dim_inputs[start]))
                    start = index
            dim_groups = tuple(dim_groups)
        max_outputs = self._fused_band_split_max_outputs()
        fused_groups = []
        for group_start, group_end, dim_in in dim_groups:
            for start in range(group_start, group_end, max_outputs):
                end = min(start + max_outputs, group_end)
                offset_start = int(dim_offsets[start])
                offset_end = int(dim_offsets[end])
                group_dim_inputs = tuple(dim_inputs[start:end])
                if len(set(group_dim_inputs)) != 1:
                    raise ValueError("private_ane grouped band split only supports contiguous equal-width groups")
                fused_groups.append((start, end, int(dim_in), offset_start, offset_end, group_dim_inputs))

        outs = [np.empty((1, TIME_SEQ, BAND_COUNT, DIM), dtype=np.float16) for _ in xs]
        total_compile = 0.0
        total_eval = 0.0
        total_write = 0.0
        total_pack = 0.0
        total_free = 0.0
        total_gc = 0.0
        cache_hits = 0
        bridge_profile_totals: dict[str, float] = {}
        use_band_split_load_cache = bool(getattr(self.module, "private_ane_load_cache", False))

        def _make_tile(x: np.ndarray, offset_start: int, offset_end: int, tile_start: int, tile_end: int):
            valid = tile_end - tile_start
            tile = np.zeros((1, offset_end - offset_start, 1, TILE_SEQ), dtype=np.float16)
            tile[..., :valid] = x[:, offset_start:offset_end, :, tile_start:tile_end].astype(np.float16)
            return tile, valid

        for start, end, dim_in, offset_start, offset_end, group_dim_inputs in fused_groups:
            group_count = end - start
            group_input_dim = offset_end - offset_start
            output_shapes = [(1, DIM, 1, TILE_SEQ)] * group_count
            output_bytes = [DIM * TILE_SEQ * 2] * group_count
            handle = None
            try:
                if self._persistent_aux_handles():
                    handle, compile_sec, cache_hit = self._compile_persistent_bridge_multi_outputs(
                        self._band_split_handle_cache,
                        ("l2_fused_group", start, end, dim_in, TILE_SEQ),
                        f"band_split_l2_fused_{start}_{end}",
                        _band_split_l2_tile_mil(group_dim_inputs, TILE_SEQ),
                        _band_split_weights_range(self.module, start, end),
                        group_input_dim * TILE_SEQ * 2,
                        output_bytes,
                        use_load_cache=use_band_split_load_cache,
                    )
                    cache_hits += int(cache_hit)
                    profile = self._bridge_last_compile_profile(compile_sec, handle_cache_hit=cache_hit)
                else:
                    started = time.perf_counter()
                    handle = self._compile_bridge_multi_outputs(
                        f"band_split_l2_fused_{start}_{end}",
                        _band_split_l2_tile_mil(group_dim_inputs, TILE_SEQ),
                        _band_split_weights_range(self.module, start, end),
                        group_input_dim * TILE_SEQ * 2,
                        output_bytes,
                        use_load_cache=use_band_split_load_cache,
                    )
                    compile_sec = time.perf_counter() - started
                    profile = self._bridge_last_compile_profile(compile_sec)
                total_compile += compile_sec
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                for x, out in zip(xs, outs, strict=True):
                    for tile_start in range(0, TIME_SEQ, TILE_SEQ):
                        tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
                        pack_started = time.perf_counter()
                        tile, valid = _make_tile(x, offset_start, offset_end, tile_start, tile_end)
                        total_pack += time.perf_counter() - pack_started
                        eval_started = time.perf_counter()
                        bands = self.bridge.run_multi_outputs(handle, tile, output_shapes)
                        total_eval += time.perf_counter() - eval_started
                        write_started = time.perf_counter()
                        for local_index, band in enumerate(bands):
                            band_index = start + local_index
                            out[:, tile_start:tile_end, band_index, :] = (
                                band[..., :valid].reshape(1, DIM, valid).transpose(0, 2, 1)
                            )
                        total_write += time.perf_counter() - write_started
            finally:
                if handle is not None and not self._persistent_aux_handles():
                    free_sec, gc_sec = self._profile_free_handle(handle, family="band_split_fused")
                    total_free += free_sec
                    total_gc += gc_sec
                elif not self._persistent_aux_handles():
                    total_gc += self._profile_gc()
        self.last_band_split_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "write_sec": float(total_write),
            "pack_sec": float(total_pack),
            "free_sec": float(total_free),
            "gc_sec": float(total_gc),
            "wall_sec": float(time.perf_counter() - wall_started),
            "prescale_sec": 0.0,
            "tile_seq": TILE_SEQ,
            "input_target_max": None,
            "rmsnorm": "reduce_l2_norm",
            "chunks": len(xs),
            "input_prescale": "none",
            "cache_hits": int(cache_hits),
            "fused": True,
            "fused_layout": "multi_output_l2",
            "fused_groups": len(fused_groups),
            "max_outputs_per_group": max_outputs,
            "outputs": BAND_COUNT,
        }
        self.last_band_split_timing.update(bridge_profile_totals)
        return outs

    def run_band_split_l2norm_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        wall_started = time.perf_counter()
        xs = [np.ascontiguousarray(x, dtype=np.float32) for x in xs]
        for x in xs:
            if x.shape != (1, INPUT_DIM, 1, TIME_SEQ):
                raise ValueError(f"private_ane band split expects (1,{INPUT_DIM},1,{TIME_SEQ}), got {x.shape}")
        if not xs:
            return []
        outs = [np.empty((1, TIME_SEQ, BAND_COUNT, DIM), dtype=np.float16) for _ in xs]
        total_compile = 0.0
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        total_free = 0.0
        total_gc = 0.0
        cache_hits = 0
        bridge_profile_totals: dict[str, float] = {}
        offset = 0
        for band_index, (dim_in, to_feature) in enumerate(zip(self.module.band_split.dim_inputs, self.module.band_split.to_features, strict=True)):
            handle = None
            try:
                if self._persistent_aux_handles():
                    handle, compile_sec, cache_hit = self._compile_persistent_bridge(
                        self._band_split_handle_cache,
                        ("l2", band_index, dim_in, TILE_SEQ),
                        f"band_split_l2_{band_index}",
                        _band_feature_l2_tile_mil(dim_in, TILE_SEQ),
                        _band_feature_weights(to_feature),
                        dim_in * TILE_SEQ * 2,
                        DIM * TILE_SEQ * 2,
                    )
                    cache_hits += int(cache_hit)
                    profile = self._bridge_last_compile_profile(compile_sec, handle_cache_hit=cache_hit)
                else:
                    started = time.perf_counter()
                    handle = self._compile_bridge(
                        f"band_split_l2_{band_index}",
                        _band_feature_l2_tile_mil(dim_in, TILE_SEQ),
                        _band_feature_weights(to_feature),
                        dim_in * TILE_SEQ * 2,
                        DIM * TILE_SEQ * 2,
                    )
                    compile_sec = time.perf_counter() - started
                    profile = self._bridge_last_compile_profile(compile_sec)
                total_compile += compile_sec
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                for x, out in zip(xs, outs, strict=True):
                    eval_sec, pack_sec, write_sec = self._run_band_l2norm_with_handle(
                        handle,
                        x,
                        out,
                        band_index,
                        dim_in,
                        offset,
                    )
                    total_eval += eval_sec
                    total_pack += pack_sec
                    total_write += write_sec
            finally:
                if handle is not None and not self._persistent_aux_handles():
                    free_sec, gc_sec = self._profile_free_handle(handle, family="band_split")
                    total_free += free_sec
                    total_gc += gc_sec
                else:
                    total_gc += self._profile_gc()
            offset += dim_in
        self.last_band_split_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "pack_sec": float(total_pack),
            "write_sec": float(total_write),
            "free_sec": float(total_free),
            "gc_sec": float(total_gc),
            "wall_sec": float(time.perf_counter() - wall_started),
            "prescale_sec": 0.0,
            "tile_seq": TILE_SEQ,
            "input_target_max": None,
            "rmsnorm": "reduce_l2_norm",
            "chunks": len(xs),
            "input_prescale": "none",
            "cache_hits": int(cache_hits),
        }
        self.last_band_split_timing.update(bridge_profile_totals)
        return outs

    def _run_band_l2norm_with_handle(
            self,
            handle,
            x: np.ndarray,
            out: np.ndarray,
            band_index: int,
            dim_in: int,
            offset: int,
    ) -> tuple[float, float, float]:
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        for tile_start in range(0, TIME_SEQ, TILE_SEQ):
            tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
            valid = tile_end - tile_start
            pack_started = time.perf_counter()
            tile = np.zeros((1, dim_in, 1, TILE_SEQ), dtype=np.float16)
            tile[..., :valid] = x[:, offset:offset + dim_in, :, tile_start:tile_end].astype(np.float16)
            total_pack += time.perf_counter() - pack_started
            eval_started = time.perf_counter()
            band = self.bridge.run(handle, tile, (1, DIM, 1, TILE_SEQ))
            total_eval += time.perf_counter() - eval_started
            write_started = time.perf_counter()
            out[:, tile_start:tile_end, band_index, :] = band[..., :valid].reshape(1, DIM, valid).transpose(0, 2, 1)
            total_write += time.perf_counter() - write_started
        return total_eval, total_pack, total_write

    def run_band_split_l2norm_prescaled_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        xs = [np.ascontiguousarray(x, dtype=np.float32) for x in xs]
        for x in xs:
            if x.shape != (1, INPUT_DIM, 1, TIME_SEQ):
                raise ValueError(f"private_ane band split expects (1,{INPUT_DIM},1,{TIME_SEQ}), got {x.shape}")
        if not xs:
            return []
        outs = [np.empty((1, TIME_SEQ, BAND_COUNT, DIM), dtype=np.float16) for _ in xs]
        total_compile = 0.0
        total_eval = 0.0
        total_prescale = 0.0
        offset = 0
        for band_index, (dim_in, to_feature) in enumerate(zip(self.module.band_split.dim_inputs, self.module.band_split.to_features, strict=True)):
            handle = None
            started = time.perf_counter()
            try:
                handle = self._compile_bridge(
                    f"band_split_l2_prescaled_{band_index}",
                    _band_feature_l2_tile_mil(dim_in, TILE_SEQ),
                    _band_feature_weights(to_feature),
                    dim_in * TILE_SEQ * 2,
                    DIM * TILE_SEQ * 2,
                )
                total_compile += time.perf_counter() - started
                for x, out in zip(xs, outs, strict=True):
                    eval_sec, prescale_sec = self._run_band_l2norm_prescaled_with_handle(
                        handle,
                        x,
                        out,
                        band_index,
                        dim_in,
                        offset,
                    )
                    total_eval += eval_sec
                    total_prescale += prescale_sec
            finally:
                if handle is not None:
                    self.bridge.free(handle)
                gc.collect()
            offset += dim_in
        self.last_band_split_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "prescale_sec": float(total_prescale),
            "tile_seq": TILE_SEQ,
            "input_target_max": BAND_INPUT_TARGET_MAX,
            "rmsnorm": "reduce_l2_norm",
            "chunks": len(xs),
        }
        return outs

    def _run_band_l2norm_prescaled_with_handle(
            self,
            handle,
            x: np.ndarray,
            out: np.ndarray,
            band_index: int,
            dim_in: int,
            offset: int,
    ) -> tuple[float, float]:
        total_eval = 0.0
        total_prescale = 0.0
        for tile_start in range(0, TIME_SEQ, TILE_SEQ):
            tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
            valid = tile_end - tile_start
            prescale_started = time.perf_counter()
            tile_src = x[:, offset:offset + dim_in, :, tile_start:tile_end]
            abs_max = np.max(np.abs(tile_src), axis=1, keepdims=True)
            scale = np.maximum(np.float32(1.0), np.float32(BAND_INPUT_TARGET_MAX) / np.maximum(abs_max, np.float32(1e-30)))
            tile = np.zeros((1, dim_in, 1, TILE_SEQ), dtype=np.float16)
            tile[..., :valid] = (tile_src * scale).astype(np.float16)
            total_prescale += time.perf_counter() - prescale_started
            eval_started = time.perf_counter()
            band = self.bridge.run(handle, tile, (1, DIM, 1, TILE_SEQ))
            total_eval += time.perf_counter() - eval_started
            out[:, tile_start:tile_end, band_index, :] = band[..., :valid].reshape(1, DIM, valid).transpose(0, 2, 1)
        return total_eval, total_prescale

    def run_band_split_l2norm_prescaled_legacy(self, x: np.ndarray) -> np.ndarray:
        x = np.ascontiguousarray(x, dtype=np.float32)
        if x.shape != (1, INPUT_DIM, 1, TIME_SEQ):
            raise ValueError(f"private_ane band split expects (1,{INPUT_DIM},1,{TIME_SEQ}), got {x.shape}")
        out = np.empty((1, TIME_SEQ, BAND_COUNT, DIM), dtype=np.float16)
        total_compile = 0.0
        total_eval = 0.0
        total_prescale = 0.0
        offset = 0
        for band_index, (dim_in, to_feature) in enumerate(zip(self.module.band_split.dim_inputs, self.module.band_split.to_features, strict=True)):
            started = time.perf_counter()
            handle = self._compile_bridge(
                f"band_split_l2_legacy_{band_index}",
                _band_feature_l2_tile_mil(dim_in, TILE_SEQ),
                _band_feature_weights(to_feature),
                dim_in * TILE_SEQ * 2,
                DIM * TILE_SEQ * 2,
            )
            total_compile += time.perf_counter() - started
            try:
                for tile_start in range(0, TIME_SEQ, TILE_SEQ):
                    tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
                    valid = tile_end - tile_start
                    prescale_started = time.perf_counter()
                    tile_src = x[:, offset:offset + dim_in, :, tile_start:tile_end]
                    abs_max = np.max(np.abs(tile_src), axis=1, keepdims=True)
                    scale = np.maximum(np.float32(1.0), np.float32(BAND_INPUT_TARGET_MAX) / np.maximum(abs_max, np.float32(1e-30)))
                    tile = np.zeros((1, dim_in, 1, TILE_SEQ), dtype=np.float16)
                    tile[..., :valid] = (tile_src * scale).astype(np.float16)
                    total_prescale += time.perf_counter() - prescale_started
                    eval_started = time.perf_counter()
                    band = self.bridge.run(handle, tile, (1, DIM, 1, TILE_SEQ))
                    total_eval += time.perf_counter() - eval_started
                    out[:, tile_start:tile_end, band_index, :] = band[..., :valid].reshape(1, DIM, valid).transpose(0, 2, 1)
            finally:
                self.bridge.free(handle)
                gc.collect()
            offset += dim_in
        self.last_band_split_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "prescale_sec": float(total_prescale),
            "tile_seq": TILE_SEQ,
            "input_target_max": BAND_INPUT_TARGET_MAX,
            "rmsnorm": "reduce_l2_norm",
        }
        return out

    def run_final_norm(self, x: np.ndarray) -> np.ndarray:
        x = np.ascontiguousarray(x.reshape(TIME_SEQ * FREQ_SEQ, DIM, 1, 1), dtype=np.float16)
        started = time.perf_counter()
        handle = self._compile_bridge(
            "final_norm_full",
            _final_norm_mil(TIME_SEQ, FREQ_SEQ),
            _final_norm_weights(self.module),
            x.nbytes,
            x.nbytes,
        )
        compile_sec = time.perf_counter() - started
        try:
            eval_started = time.perf_counter()
            out = self.bridge.run(handle, x, x.shape)
            eval_sec = time.perf_counter() - eval_started
        finally:
            self.bridge.free(handle)
            gc.collect()
        self.last_final_norm_timing = {"compile_sec": float(compile_sec), "eval_sec": float(eval_sec)}
        return out.reshape(1, TIME_SEQ, FREQ_SEQ, DIM).astype(np.float16, copy=False)

    def run_final_norm_tiled(self, x: np.ndarray) -> np.ndarray:
        wall_started = time.perf_counter()
        x = np.ascontiguousarray(x, dtype=np.float16)
        if x.shape != (1, TIME_SEQ, FREQ_SEQ, DIM):
            raise ValueError(f"private_ane final norm expects (1,{TIME_SEQ},{FREQ_SEQ},{DIM}), got {x.shape}")
        handle = None
        started = time.perf_counter()
        free_sec = 0.0
        gc_sec = 0.0
        try:
            handle = self._compile_bridge(
                "final_norm_tiled",
                _norm_tile_mil(FREQ_SEQ, TILE_SEQ),
                _final_norm_weights(self.module),
                FREQ_SEQ * DIM * TILE_SEQ * 2,
                FREQ_SEQ * DIM * TILE_SEQ * 2,
            )
            compile_sec = time.perf_counter() - started
            out, eval_sec, pack_sec, write_sec = self._run_final_norm_tiled_with_handle(handle, x)
        finally:
            if handle is not None:
                free_sec, gc_sec = self._profile_free_handle(handle, family="final_norm_tiled")
            else:
                gc_sec = self._profile_gc()
        self.last_final_norm_timing = {
            "compile_sec": float(compile_sec),
            "eval_sec": float(eval_sec),
            "pack_sec": float(pack_sec),
            "write_sec": float(write_sec),
            "free_sec": float(free_sec),
            "gc_sec": float(gc_sec),
            "wall_sec": float(time.perf_counter() - wall_started),
            "tile_seq": TILE_SEQ,
        }
        return out

    def run_final_norm_tiled_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        wall_started = time.perf_counter()
        xs = [np.ascontiguousarray(x, dtype=np.float16) for x in xs]
        for x in xs:
            if x.shape != (1, TIME_SEQ, FREQ_SEQ, DIM):
                raise ValueError(f"private_ane final norm expects (1,{TIME_SEQ},{FREQ_SEQ},{DIM}), got {x.shape}")
        if not xs:
            return []
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        free_sec = 0.0
        gc_sec = 0.0
        bridge_profile_totals: dict[str, float] = {}
        handle = None
        try:
            if self._persistent_aux_handles():
                handle, compile_sec, cache_hit = self._compile_persistent_bridge(
                    self._final_norm_handle_cache,
                    ("tiled_many", FREQ_SEQ, TILE_SEQ),
                    "final_norm_tiled_many",
                    _norm_tile_mil(FREQ_SEQ, TILE_SEQ),
                    _final_norm_weights(self.module),
                    FREQ_SEQ * DIM * TILE_SEQ * 2,
                    FREQ_SEQ * DIM * TILE_SEQ * 2,
                )
                profile = self._bridge_last_compile_profile(compile_sec, handle_cache_hit=cache_hit)
            else:
                started = time.perf_counter()
                handle = self._compile_bridge(
                    "final_norm_tiled_many",
                    _norm_tile_mil(FREQ_SEQ, TILE_SEQ),
                    _final_norm_weights(self.module),
                    FREQ_SEQ * DIM * TILE_SEQ * 2,
                    FREQ_SEQ * DIM * TILE_SEQ * 2,
                )
                compile_sec = time.perf_counter() - started
                cache_hit = False
                profile = self._bridge_last_compile_profile(compile_sec)
            _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
            outs = []
            for x in xs:
                out, eval_sec, pack_sec, write_sec = self._run_final_norm_tiled_with_handle(handle, x)
                total_eval += eval_sec
                total_pack += pack_sec
                total_write += write_sec
                outs.append(out)
        finally:
            if handle is not None and not self._persistent_aux_handles():
                free_sec, gc_sec = self._profile_free_handle(handle, family="final_norm_tiled_many")
            else:
                gc_sec = self._profile_gc()
        self.last_final_norm_timing = {
            "compile_sec": float(compile_sec),
            "eval_sec": float(total_eval),
            "pack_sec": float(total_pack),
            "write_sec": float(total_write),
            "free_sec": float(free_sec),
            "gc_sec": float(gc_sec),
            "wall_sec": float(time.perf_counter() - wall_started),
            "tile_seq": TILE_SEQ,
            "chunks": len(xs),
            "cache_hits": int(cache_hit),
        }
        self.last_final_norm_timing.update(bridge_profile_totals)
        return outs

    def _run_final_norm_tiled_with_handle(self, handle, x: np.ndarray) -> tuple[np.ndarray, float, float, float]:
        flat = x.reshape(TIME_SEQ, FREQ_SEQ, DIM).transpose(1, 2, 0)
        out = np.empty_like(flat)
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        for tile_start in range(0, TIME_SEQ, TILE_SEQ):
            tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
            valid = tile_end - tile_start
            pack_started = time.perf_counter()
            tile = np.zeros((FREQ_SEQ, DIM, 1, TILE_SEQ), dtype=np.float16)
            tile[..., :valid] = flat[:, :, tile_start:tile_end].reshape(FREQ_SEQ, DIM, 1, valid)
            total_pack += time.perf_counter() - pack_started
            eval_started = time.perf_counter()
            y = self.bridge.run(handle, tile, tile.shape)
            total_eval += time.perf_counter() - eval_started
            write_started = time.perf_counter()
            out[:, :, tile_start:tile_end] = y[..., :valid].reshape(FREQ_SEQ, DIM, valid)
            total_write += time.perf_counter() - write_started
        out = out.transpose(2, 0, 1).reshape(1, TIME_SEQ, FREQ_SEQ, DIM).astype(np.float16, copy=False)
        return out, total_eval, total_pack, total_write

    def run_mask_estimator_tiled(self, x: np.ndarray) -> np.ndarray:
        return self.run_mask_estimator_tiled_many([x])[0]

    def run_mask_estimator_tiled_fused_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        wall_started = time.perf_counter()
        xs = [np.ascontiguousarray(x, dtype=np.float16) for x in xs]
        for x in xs:
            if x.shape != (1, TIME_SEQ, FREQ_SEQ, DIM):
                raise ValueError(f"private_ane mask estimator expects (1,{TIME_SEQ},{FREQ_SEQ},{DIM}), got {x.shape}")
        if not xs:
            return []
        if self.module._active_source_count() != 1:
            raise NotImplementedError("private_ane mask estimator supports one active source")
        estimator = self.module._active_mask_estimators()[0]
        dim_inputs = tuple(int(dim) for dim in estimator.dim_inputs)
        if len(dim_inputs) != BAND_COUNT or sum(dim_inputs) != MASK_DIM:
            raise ValueError(
                f"private_ane fused mask expects {BAND_COUNT} bands summing to {MASK_DIM}, "
                f"got {len(dim_inputs)} bands summing to {sum(dim_inputs)}"
            )
        band_layers = estimator._band_groupable_layers()
        if any(layers is None for layers in band_layers):
            raise ValueError("private_ane fused mask requires groupable two-linear mask bands")
        for layers in band_layers:
            if len(layers) != 3 or layers[0][0] != "linear" or layers[1][0] != "tanh" or layers[2][0] != "linear":
                raise ValueError("private_ane fused mask supports linear/tanh/linear mask bands only")

        dim_offsets = getattr(estimator, "_dim_offsets", None)
        if dim_offsets is None:
            dim_offsets = (0, *np.cumsum(np.array(dim_inputs, dtype=np.int64)).tolist())
        dim_groups = getattr(estimator, "_dim_groups", None)
        if dim_groups is None:
            dim_groups = []
            start = 0
            for index in range(1, len(dim_inputs) + 1):
                if index == len(dim_inputs) or dim_inputs[index] != dim_inputs[start]:
                    dim_groups.append((start, index, dim_inputs[start]))
                    start = index
            dim_groups = tuple(dim_groups)

        max_outputs = self._fused_mask_max_outputs()
        fused_groups = []
        for group_start, group_end, dim_in in dim_groups:
            for start in range(group_start, group_end, max_outputs):
                end = min(start + max_outputs, group_end)
                if len(set(dim_inputs[start:end])) != 1:
                    raise ValueError("private_ane fused mask only supports contiguous equal-width groups")
                fused_groups.append((start, end, int(dim_in), int(dim_offsets[start]), int(dim_offsets[end])))

        results = [np.empty((1, 1, TIME_SEQ, MASK_DIM), dtype=np.float16) for _ in xs]
        total_compile = 0.0
        total_eval = 0.0
        total_write = 0.0
        total_pack = 0.0
        total_group_pack = 0.0
        total_free = 0.0
        total_gc = 0.0
        cache_hits = 0
        bridge_profile_totals: dict[str, float] = {}
        use_mask_load_cache = bool(getattr(self.module, "private_ane_load_cache", False))
        for start, end, dim_in, offset_start, _offset_end in fused_groups:
            group_count = end - start
            group_input_dim = group_count * DIM
            group_output_dim = group_count * dim_in
            handle = None
            try:
                if self._persistent_aux_handles():
                    handle, compile_sec, cache_hit = self._compile_persistent_bridge(
                        self._mask_handle_cache,
                        ("mask_fused_grouped_conv", start, end, dim_in, TILE_SEQ),
                        f"mask_fused_{start}_{end}",
                        _mask_grouped_conv_mil(dim_in, group_count, TILE_SEQ),
                        _mask_grouped_conv_weights_range(estimator, start, end),
                        group_input_dim * TILE_SEQ * 2,
                        group_output_dim * TILE_SEQ * 2,
                        use_load_cache=use_mask_load_cache,
                    )
                    cache_hits += int(cache_hit)
                    profile = self._bridge_last_compile_profile(compile_sec, handle_cache_hit=cache_hit)
                else:
                    started = time.perf_counter()
                    handle = self._compile_bridge(
                        f"mask_fused_{start}_{end}",
                        _mask_grouped_conv_mil(dim_in, group_count, TILE_SEQ),
                        _mask_grouped_conv_weights_range(estimator, start, end),
                        group_input_dim * TILE_SEQ * 2,
                        group_output_dim * TILE_SEQ * 2,
                        use_load_cache=use_mask_load_cache,
                    )
                    compile_sec = time.perf_counter() - started
                    profile = self._bridge_last_compile_profile(compile_sec)
                total_compile += compile_sec
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                for x, result in zip(xs, results, strict=True):
                    group_pack_started = time.perf_counter()
                    group_x = x[:, :, start:end, :].transpose(0, 2, 3, 1).reshape(1, group_input_dim, 1, TIME_SEQ)
                    total_group_pack += time.perf_counter() - group_pack_started
                    for tile_start in range(0, TIME_SEQ, TILE_SEQ):
                        tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
                        valid = tile_end - tile_start
                        pack_started = time.perf_counter()
                        tile = np.zeros((1, group_input_dim, 1, TILE_SEQ), dtype=np.float16)
                        tile[..., :valid] = group_x[..., tile_start:tile_end]
                        total_pack += time.perf_counter() - pack_started
                        eval_started = time.perf_counter()
                        group_out = self.bridge.run(handle, tile, (1, group_output_dim, 1, TILE_SEQ))
                        total_eval += time.perf_counter() - eval_started
                        write_started = time.perf_counter()
                        for local_index in range(group_count):
                            band_index = start + local_index
                            band_offset = int(dim_offsets[band_index])
                            local_offset = local_index * dim_in
                            band = group_out[:, local_offset:local_offset + dim_in, :, :]
                            result[:, 0, tile_start:tile_end, band_offset:band_offset + dim_in] = (
                                band[..., :valid].reshape(1, dim_in, valid).transpose(0, 2, 1)
                            )
                        total_write += time.perf_counter() - write_started
            finally:
                if handle is not None and not self._persistent_aux_handles():
                    free_sec, gc_sec = self._profile_free_handle(handle, family="mask_fused")
                    total_free += free_sec
                    total_gc += gc_sec
                elif not self._persistent_aux_handles():
                    total_gc += self._profile_gc()
        self.last_mask_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "write_sec": float(total_write),
            "pack_sec": float(total_pack),
            "group_pack_sec": float(total_group_pack),
            "free_sec": float(total_free),
            "gc_sec": float(total_gc),
            "wall_sec": float(time.perf_counter() - wall_started),
            "tile_seq": TILE_SEQ,
            "chunks": len(xs),
            "cache_hits": int(cache_hits),
            "load_cache_enabled": bool(use_mask_load_cache),
            "fused": True,
            "fused_layout": "grouped_conv",
            "fused_groups": len(fused_groups),
            "max_outputs_per_group": max_outputs,
            "outputs": BAND_COUNT,
        }
        self.last_mask_timing.update(bridge_profile_totals)
        return results

    def run_mask_estimator_tiled_many(self, xs: list[np.ndarray]) -> list[np.ndarray]:
        wall_started = time.perf_counter()
        xs = [np.ascontiguousarray(x, dtype=np.float16) for x in xs]
        for x in xs:
            if x.shape != (1, TIME_SEQ, FREQ_SEQ, DIM):
                raise ValueError(f"private_ane mask estimator expects (1,{TIME_SEQ},{FREQ_SEQ},{DIM}), got {x.shape}")
        if not xs:
            return []
        if self.module._active_source_count() != 1:
            raise NotImplementedError("private_ane mask estimator supports one active source")
        estimator = self.module._active_mask_estimators()[0]
        results = [np.empty((1, 1, TIME_SEQ, MASK_DIM), dtype=np.float16) for _ in xs]
        total_compile = 0.0
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        total_free = 0.0
        total_gc = 0.0
        cache_hits = 0
        bridge_profile_totals: dict[str, float] = {}
        offset = 0
        for band_index, dim_in in enumerate(estimator.dim_inputs):
            handle = None
            try:
                if self._persistent_aux_handles():
                    handle, compile_sec, cache_hit = self._compile_persistent_bridge(
                        self._mask_handle_cache,
                        ("mask", band_index, dim_in, TILE_SEQ),
                        f"mask_band_{band_index}",
                        _mask_band_mil(dim_in, TILE_SEQ),
                        _mask_band_weights(estimator, band_index),
                        DIM * TILE_SEQ * 2,
                        dim_in * TILE_SEQ * 2,
                    )
                    cache_hits += int(cache_hit)
                    profile = self._bridge_last_compile_profile(compile_sec, handle_cache_hit=cache_hit)
                else:
                    started = time.perf_counter()
                    handle = self._compile_bridge(
                        f"mask_band_{band_index}",
                        _mask_band_mil(dim_in, TILE_SEQ),
                        _mask_band_weights(estimator, band_index),
                        DIM * TILE_SEQ * 2,
                        dim_in * TILE_SEQ * 2,
                    )
                    compile_sec = time.perf_counter() - started
                    profile = self._bridge_last_compile_profile(compile_sec)
                total_compile += compile_sec
                _accumulate_bridge_profile_totals(bridge_profile_totals, profile)
                for x, result in zip(xs, results, strict=True):
                    eval_sec, pack_sec, write_sec = self._run_mask_band_tiled_with_handle(
                        handle,
                        x,
                        result,
                        band_index,
                        dim_in,
                        offset,
                    )
                    total_eval += eval_sec
                    total_pack += pack_sec
                    total_write += write_sec
            finally:
                if handle is not None and not self._persistent_aux_handles():
                    free_sec, gc_sec = self._profile_free_handle(handle, family="mask")
                    total_free += free_sec
                    total_gc += gc_sec
                elif not self._persistent_aux_handles():
                    total_gc += self._profile_gc()
            offset += dim_in
        self.last_mask_timing = {
            "compile_sec": float(total_compile),
            "eval_sec": float(total_eval),
            "pack_sec": float(total_pack),
            "write_sec": float(total_write),
            "free_sec": float(total_free),
            "gc_sec": float(total_gc),
            "wall_sec": float(time.perf_counter() - wall_started),
            "tile_seq": TILE_SEQ,
            "chunks": len(xs),
            "cache_hits": int(cache_hits),
        }
        self.last_mask_timing.update(bridge_profile_totals)
        return results

    def _run_mask_band_tiled_with_handle(
            self,
            handle,
            x: np.ndarray,
            result: np.ndarray,
            band_index: int,
            dim_in: int,
            offset: int,
    ) -> tuple[float, float, float]:
        total_eval = 0.0
        total_pack = 0.0
        total_write = 0.0
        band_x = x[:, :, band_index, :]
        for tile_start in range(0, TIME_SEQ, TILE_SEQ):
            tile_end = min(tile_start + TILE_SEQ, TIME_SEQ)
            valid = tile_end - tile_start
            pack_started = time.perf_counter()
            tile = np.zeros((1, DIM, 1, TILE_SEQ), dtype=np.float16)
            tile[..., :valid] = band_x[:, tile_start:tile_end, :].transpose(0, 2, 1).reshape(1, DIM, 1, valid)
            total_pack += time.perf_counter() - pack_started
            eval_started = time.perf_counter()
            y = self.bridge.run(handle, tile, (1, dim_in, 1, TILE_SEQ))
            total_eval += time.perf_counter() - eval_started
            write_started = time.perf_counter()
            result[:, 0, tile_start:tile_end, offset:offset + dim_in] = (
                y[..., :valid].reshape(1, dim_in, valid).transpose(0, 2, 1)
            )
            total_write += time.perf_counter() - write_started
        return total_eval, total_pack, total_write


def _runner(module) -> PrivateANETransformerRunner:
    runner = getattr(module, "_private_ane_runner", None)
    if runner is None:
        runner = PrivateANETransformerRunner(module)
        module._private_ane_runner = runner
    return runner


def _allow_torch_fallback(module) -> bool:
    value = getattr(module, "private_ane_allow_torch_fallback", False)
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def _private_ane_gpu_tail_dtype(module):
    dtype = getattr(module, "mps_model_compute_dtype", torch.float16)
    if isinstance(dtype, str):
        normalized = dtype.lower()
        if normalized in ("float16", "fp16", "half"):
            return torch.float16
        if normalized in ("float32", "fp32", "single"):
            return torch.float32
    if dtype not in (torch.float16, torch.float32):
        raise TypeError(f"private_ane GPU tail supports torch.float16 or torch.float32, got {dtype}")
    return dtype


def _private_ane_torch_final_norm_mask_many(
        module,
        xs: list[np.ndarray],
        references: list[torch.Tensor],
        stage: str = "torch_fp16",
) -> tuple[list[torch.Tensor], dict, dict]:
    wall_started = time.perf_counter()
    xs_t = [torch.from_numpy(x_np).to(device="cpu", dtype=torch.float16) for x_np in xs]
    norm_started = time.perf_counter()
    xs_t = [module.final_norm(x) for x in xs_t]
    norm_sec = time.perf_counter() - norm_started
    mask_started = time.perf_counter()
    masks = []
    for x, reference in zip(xs_t, references, strict=True):
        mask = mask_to_complex_shape(module._estimate_masks(x), complex_dim=2)
        masks.append(mask.to(device=reference.device, dtype=reference.dtype))
    mask_sec = time.perf_counter() - mask_started
    wall_sec = time.perf_counter() - wall_started
    final_norm_timing = {
        "stage": stage,
        "wall_sec": float(norm_sec),
        "chunks": int(len(xs)),
        "included_wall_sec": float(wall_sec),
    }
    mask_timing = {
        "stage": stage,
        "wall_sec": float(mask_sec),
        "chunks": int(len(xs)),
        "included_wall_sec": float(wall_sec),
    }
    return masks, final_norm_timing, mask_timing


def _private_ane_mlx_final_norm_mask_many(
        module,
        xs: list[np.ndarray],
        references: list[torch.Tensor],
) -> tuple[list[torch.Tensor], dict, dict]:
    from .mlx_roformer import mlx_final_norm_mask_many_to_torch

    masks, timing = mlx_final_norm_mask_many_to_torch(
        module,
        xs,
        references,
        dtype=_private_ane_gpu_tail_dtype(module),
    )
    final_norm_timing = {
        "stage": "mlx_gpu",
        "wall_sec": 0.0,
        "chunks": int(len(xs)),
        "included_in": "mask",
        "included_stage": "mlx_gpu_final_norm_mask",
    }
    mask_timing = dict(timing)
    mask_timing["stage"] = "mlx_gpu_final_norm_mask"
    return masks, final_norm_timing, mask_timing


def private_ane_stft_roformer(module, raw_audio: torch.Tensor) -> tuple[torch.Tensor, SpectralContext]:
    if raw_audio.ndim != 2:
        raise ValueError(f"private_ane STFT expects chunk shape (channels,samples), got {tuple(raw_audio.shape)}")
    if not module.stereo or raw_audio.shape[0] != 2:
        raise NotImplementedError("private_ane STFT currently supports stereo RoFormer chunks only")
    if (
        int(module.stft_kwargs["n_fft"]) != STFT_N_FFT
        or int(module.stft_kwargs["hop_length"]) != STFT_HOP
        or int(module.stft_kwargs["win_length"]) != STFT_N_FFT
        or bool(module.stft_kwargs.get("normalized", False))
    ):
        raise NotImplementedError("private_ane STFT currently supports n_fft=2048 hop=512 win=2048 normalized=False")
    runner = _runner(module)
    preload_timing = runner.maybe_preload_stft_handles()
    if preload_timing is not None:
        module._pymss_private_ane_last_stft_preload = dict(preload_timing)
    stft_np, timing = runner.run_stft_channel_seq(raw_audio.detach().cpu().numpy())
    stft_window = module.stft_window(torch.device("cpu"))
    context = SpectralContext(
        batch=1,
        channels=2,
        freq_bins=STFT_FREQ_BINS,
        audio_length=raw_audio.shape[-1],
        stft_window=stft_window,
        x_is_mps=False,
    )
    module._pymss_private_ane_last_stft = timing
    return torch.from_numpy(stft_np).to(device="cpu", dtype=torch.float32), context


def _private_ane_overlap_add(frames: np.ndarray, length: int) -> np.ndarray:
    window = torch.hann_window(STFT_N_FFT).numpy().astype(np.float32)
    frames = frames * window[None, None, :]
    full_length = STFT_N_FFT + STFT_HOP * (TIME_SEQ - 1)
    audio = np.zeros((2, full_length), dtype=np.float32)
    denom = np.zeros((full_length,), dtype=np.float32)
    win_sq = window * window
    for frame_index in range(TIME_SEQ):
        start = frame_index * STFT_HOP
        audio[:, start:start + STFT_N_FFT] += frames[:, frame_index, :]
        denom[start:start + STFT_N_FFT] += win_sq
    audio = audio / np.maximum(denom[None, :], np.float32(1e-11))
    pad = STFT_N_FFT // 2
    return np.ascontiguousarray(audio[:, pad:pad + length], dtype=np.float32)


def private_ane_istft_roformer(module, stft_repr: torch.Tensor, context: SpectralContext, length: int) -> torch.Tensor:
    if bool(getattr(module, "private_ane_gpu_istft", False)):
        try:
            from .mlx_roformer import mlx_istft_roformer_to_torch

            output, timing = mlx_istft_roformer_to_torch(
                module,
                stft_repr,
                context,
                length,
                dtype=_private_ane_gpu_tail_dtype(module),
            )
            module._pymss_private_ane_last_istft = timing
            return output
        except Exception as exc:
            if not _allow_torch_fallback(module):
                raise RuntimeError("private_ane MLX GPU ISTFT failed and torch fallback is disabled") from exc
            from .common import istft_roformer

            module._pymss_private_ane_outer_error = f"istft_mlx_gpu: {exc!r}"
            started = time.perf_counter()
            with torch.inference_mode():
                output = istft_roformer(module, stft_repr, context, length)
            module._pymss_private_ane_last_istft = {
                "stage": "torch_fallback_after_mlx_gpu_istft",
                "wall_sec": float(time.perf_counter() - started),
            }
            return output

    if context.batch != 1 or context.channels != 2 or context.freq_bins != STFT_FREQ_BINS:
        raise NotImplementedError("private_ane ISTFT currently supports single stereo RoFormer chunks only")
    if (
        int(module.stft_kwargs["n_fft"]) != STFT_N_FFT
        or int(module.stft_kwargs["hop_length"]) != STFT_HOP
        or int(module.stft_kwargs["win_length"]) != STFT_N_FFT
        or bool(module.stft_kwargs.get("normalized", False))
    ):
        raise NotImplementedError("private_ane ISTFT currently supports n_fft=2048 hop=512 win=2048 normalized=False")
    if stft_repr.shape != (1, 1, STFT_FREQ_BINS * 2, TIME_SEQ):
        raise ValueError(f"private_ane ISTFT expects (1,1,{STFT_FREQ_BINS * 2},{TIME_SEQ}), got {tuple(stft_repr.shape)}")
    stft_np = torch.view_as_real(stft_repr.detach().cpu()).numpy()
    stft_np = stft_np.reshape(1, 1, STFT_FREQ_BINS, 2, TIME_SEQ, 2)
    stft_np = np.ascontiguousarray(stft_np[0, 0].transpose(1, 0, 2, 3), dtype=np.float32)
    runner = _runner(module)
    frames, timing = runner.run_irfft_channel_seq(stft_np)
    overlap_started = time.perf_counter()
    audio = _private_ane_overlap_add(frames, int(length))
    timing = dict(timing)
    timing["overlap_add_sec"] = float(time.perf_counter() - overlap_started)
    timing["outer_wall_sec"] = float(timing.get("wall_sec", 0.0) + timing["overlap_add_sec"])
    module._pymss_private_ane_last_istft = timing
    return torch.from_numpy(audio).reshape(1, 2, audio.shape[-1])


def private_ane_forward_mask_core(module, stft_repr: torch.Tensor) -> torch.Tensor:
    if module._active_source_count() != 1:
        raise NotImplementedError("private_ane currently supports single-source BSR models only")
    if getattr(module, "mask_mode", "no_segm") != "no_segm":
        raise NotImplementedError("private_ane currently supports HyperACE mask_mode='no_segm' only")

    device = stft_repr.device
    dtype = stft_repr.dtype
    b, fs, model_t, complex_dim = stft_repr.shape
    if (b, fs, model_t, complex_dim) != (1, 2050, TIME_SEQ, 2):
        raise ValueError(f"private_ane expects stft_repr shape (1,2050,{TIME_SEQ},2), got {tuple(stft_repr.shape)}")

    runner = _runner(module)
    try:
        x_flat = stft_repr.to(device="cpu", dtype=torch.float32).permute(0, 2, 1, 3).reshape(b, model_t, fs * complex_dim)
        x_input = np.ascontiguousarray(x_flat.permute(0, 2, 1).reshape(1, INPUT_DIM, 1, TIME_SEQ).numpy())
        if bool(getattr(module, "private_ane_fused_band_split", False)):
            x_np = runner.run_band_split_l2norm_fused(x_input)
            band_split_stage = "private_ane_l2_fused"
        else:
            x_np = runner.run_band_split_l2norm(x_input)
            band_split_stage = "private_ane_l2"
    except Exception as exc:
        if not _allow_torch_fallback(module):
            raise RuntimeError("private_ane band split failed and torch fallback is disabled") from exc
        module._pymss_private_ane_outer_error = f"band_split_private_ane: {exc!r}"
        with torch.inference_mode():
            x = stft_repr.to(device="cpu", dtype=torch.float32).permute(0, 2, 1, 3).reshape(b, model_t, fs * complex_dim)
            x = module.band_split(x)
        x_np = x.detach().cpu().numpy().astype(np.float16, copy=False)
        band_split_stage = "torch_fp32"
    started = time.perf_counter()
    x_np = runner.run_transformers(x_np)
    transformer_sec = time.perf_counter() - started
    final_norm_timing = None
    mask_timing = None
    if bool(getattr(module, "private_ane_gpu_final_norm_mask", False)):
        try:
            masks, final_norm_timing, mask_timing = _private_ane_mlx_final_norm_mask_many(
                module,
                [x_np],
                [stft_repr],
            )
            mask = masks[0]
            final_norm_stage = "mlx_gpu"
            mask_stage = "mlx_gpu"
        except Exception as exc:
            if not _allow_torch_fallback(module):
                raise RuntimeError(
                    "private_ane MLX GPU final_norm/mask failed and torch fallback is disabled"
                ) from exc
            module._pymss_private_ane_outer_error = f"final_norm_mask_mlx_gpu: {exc!r}"
            with torch.inference_mode():
                masks, final_norm_timing, mask_timing = _private_ane_torch_final_norm_mask_many(
                    module,
                    [x_np],
                    [stft_repr],
                    stage="torch_fallback_after_mlx_gpu",
                )
            mask = masks[0]
            final_norm_stage = "torch_fp16"
            mask_stage = "torch_fp16"
    else:
        try:
            x_np = runner.run_final_norm_tiled(x_np)
            final_norm_stage = "private_ane"
            final_norm_timing = getattr(runner, "last_final_norm_timing", None)
        except Exception as exc:
            if not _allow_torch_fallback(module):
                raise RuntimeError("private_ane final norm failed and torch fallback is disabled") from exc
            module._pymss_private_ane_outer_error = f"final_norm_private_ane: {exc!r}"
            x_t = torch.from_numpy(x_np).to(device="cpu", dtype=torch.float16)
            with torch.inference_mode():
                norm_started = time.perf_counter()
                x_t = module.final_norm(x_t)
            final_norm_timing = {
                "stage": "torch_fp16",
                "wall_sec": float(time.perf_counter() - norm_started),
                "chunks": 1,
            }
            x_np = x_t.detach().cpu().numpy().astype(np.float16, copy=False)
            final_norm_stage = "torch_fp16"
        x = torch.from_numpy(x_np).to(device="cpu", dtype=torch.float16)

        try:
            if bool(getattr(module, "private_ane_fused_mask_estimator", False)):
                mask_np = runner.run_mask_estimator_tiled_fused_many([x_np])[0]
                mask_stage = "private_ane_fused"
            else:
                mask_np = runner.run_mask_estimator_tiled(x_np)
                mask_stage = "private_ane"
            mask = torch.from_numpy(mask_np).to(device="cpu", dtype=torch.float16)
            mask_timing = getattr(runner, "last_mask_timing", None)
        except Exception as exc:
            if not _allow_torch_fallback(module):
                raise RuntimeError("private_ane mask estimator failed and torch fallback is disabled") from exc
            module._pymss_private_ane_outer_error = f"mask_private_ane: {exc!r}"
            with torch.inference_mode():
                mask_started = time.perf_counter()
                mask = module._estimate_masks(x)
            mask_timing = {
                "stage": "torch_fp16",
                "wall_sec": float(time.perf_counter() - mask_started),
                "chunks": 1,
            }
            mask_stage = "torch_fp16"
        mask = mask_to_complex_shape(mask, complex_dim=2)
    runner.last_final_norm_timing = final_norm_timing
    runner.last_mask_timing = mask_timing

    summary_build_started = time.perf_counter()
    module._pymss_private_ane_last_timings = tuple(runner.last_timings)
    mask_batch_detail["wall_sec"] = float(time.perf_counter() - mask_batch_wall_started)
    module._pymss_private_ane_last_summary = {
        "transformer_sec": float(transformer_sec),
        "gelu_mode": runner._gelu_mode(),
        "fuse_residual": bool(runner._fuse_residual()),
        "fuse_gate_ffn": bool(runner._fuse_gate_ffn()),
        "two_input_gate": bool(runner._two_input_gate()),
        "bridge_pack_gate": bool(runner._bridge_pack_gate()),
        "surface_handoff_gate_ffn": bool(runner._surface_handoff_gate_ffn()),
        "batch_axis_eval": bool(runner._batch_axis_eval()),
        "persistent_transformer_handles": bool(
            getattr(module, "private_ane_persistent_transformer_handles", False)
        ),
        "allow_transformer_handle_cache": bool(
            getattr(module, "private_ane_allow_transformer_handle_cache", False)
        ),
        "tiled_time_attention_pre": bool(runner._tiled_time_attention_pre()),
        "tiled_time_attention_pre_q_chunk": (
            runner._tiled_time_attention_pre_q_chunk() if runner._tiled_time_attention_pre() else 0
        ),
        "fused_band_split": bool(getattr(module, "private_ane_fused_band_split", False)),
        "fused_mask_estimator": bool(getattr(module, "private_ane_fused_mask_estimator", False)),
        "gpu_final_norm_mask": bool(getattr(module, "private_ane_gpu_final_norm_mask", False)),
        "gpu_istft": bool(getattr(module, "private_ane_gpu_istft", False)),
        "torch_fallback_allowed": bool(_allow_torch_fallback(module)),
        "release_aux_handles_before_istft": bool(
            getattr(module, "private_ane_release_aux_handles_before_istft", True)
        ),
        "dynamic_stft": bool(getattr(module, "private_ane_dynamic_stft", False)),
        "outer_stages": f"{band_split_stage}_band_split_{final_norm_stage}_final_norm_{mask_stage}_mask",
        "band_split": getattr(runner, "last_band_split_timing", None),
        "final_norm": final_norm_timing,
        "mask": mask_timing,
        "stft_preload": getattr(runner, "last_stft_preload_timing", None),
        "transformer_timings": tuple(runner.last_timings),
        "memory_samples": tuple(runner.last_memory_samples),
        "bridge_load_cache": {
            "enabled": bool(getattr(runner.bridge, "use_load_cache", False)),
            "hits": int(getattr(runner.bridge, "load_cache_hits", 0)),
            "misses": int(getattr(runner.bridge, "load_cache_misses", 0)),
        },
        "free_profile_by_family": dict(getattr(runner, "_free_profile_by_family", {}) or {}),
        "final_cache_handles": runner.cache_handle_counts(),
    }
    return mask.to(device=device, dtype=dtype)


def private_ane_forward_mask_core_batch_layerwise(module, stft_reprs: list[torch.Tensor]) -> list[torch.Tensor]:
    if not stft_reprs:
        return []
    if module._active_source_count() != 1:
        raise NotImplementedError("private_ane currently supports single-source BSR models only")
    if getattr(module, "mask_mode", "no_segm") != "no_segm":
        raise NotImplementedError("private_ane currently supports HyperACE mask_mode='no_segm' only")

    runner = _runner(module)
    mask_batch_wall_started = time.perf_counter()
    mask_batch_detail = {
        "chunks": int(len(stft_reprs)),
        "input_pack_sec": 0.0,
        "band_split_outer_sec": 0.0,
        "band_split_outer_gap_sec": 0.0,
        "transformer_outer_sec": 0.0,
        "transformer_known_sec": 0.0,
        "transformer_outer_gap_sec": 0.0,
        "final_norm_outer_sec": 0.0,
        "final_norm_outer_gap_sec": 0.0,
        "mask_outer_sec": 0.0,
        "mask_outer_gap_sec": 0.0,
        "mask_output_pack_sec": 0.0,
        "summary_build_sec": 0.0,
        "wall_sec": 0.0,
    }
    x_inputs = []
    band_split_stage = "private_ane_l2"
    input_pack_started = time.perf_counter()
    for stft_repr in stft_reprs:
        b, fs, model_t, complex_dim = stft_repr.shape
        if (b, fs, model_t, complex_dim) != (1, 2050, TIME_SEQ, 2):
            raise ValueError(f"private_ane expects stft_repr shape (1,2050,{TIME_SEQ},2), got {tuple(stft_repr.shape)}")
        x_flat = stft_repr.to(device="cpu", dtype=torch.float32).permute(0, 2, 1, 3).reshape(b, model_t, fs * complex_dim)
        x_inputs.append(np.ascontiguousarray(x_flat.permute(0, 2, 1).reshape(1, INPUT_DIM, 1, TIME_SEQ).numpy()))
    mask_batch_detail["input_pack_sec"] = float(time.perf_counter() - input_pack_started)

    band_split_outer_started = time.perf_counter()
    try:
        if bool(getattr(module, "private_ane_fused_band_split", False)):
            xs = runner.run_band_split_l2norm_fused_many(x_inputs)
            band_split_stage = "private_ane_l2_fused"
        else:
            xs = runner.run_band_split_l2norm_many(x_inputs)
    except Exception as exc:
        if not _allow_torch_fallback(module):
            raise RuntimeError("private_ane batch band split failed and torch fallback is disabled") from exc
        module._pymss_private_ane_outer_error = f"band_split_private_ane: {exc!r}"
        band_split_stage = "torch_fp32"
        xs = []
        for stft_repr in stft_reprs:
            b, fs, model_t, complex_dim = stft_repr.shape
            with torch.inference_mode():
                x = stft_repr.to(device="cpu", dtype=torch.float32).permute(0, 2, 1, 3).reshape(b, model_t, fs * complex_dim)
                x = module.band_split(x)
            xs.append(x.detach().cpu().numpy().astype(np.float16, copy=False))
    mask_batch_detail["band_split_outer_sec"] = float(time.perf_counter() - band_split_outer_started)
    band_split_timing = getattr(runner, "last_band_split_timing", None)
    if isinstance(band_split_timing, dict):
        mask_batch_detail["band_split_outer_gap_sec"] = max(
            0.0,
            float(mask_batch_detail["band_split_outer_sec"]) - float(band_split_timing.get("wall_sec", 0.0) or 0.0),
        )

    started = time.perf_counter()
    xs = runner.run_transformers_layerwise_many(xs)
    transformer_sec = time.perf_counter() - started
    mask_batch_detail["transformer_outer_sec"] = float(transformer_sec)
    transformer_known_keys = (
        "load_or_compile_wall_sec",
        "eval_sec",
        "handle_free_sec",
        "gc_sec",
        "post_eval_gc_sec",
        "post_eval_guard_sec",
        "post_free_guard_sec",
        "timing_bookkeeping_sec",
        "segment_outer_gap_sec",
    )
    transformer_known_sec = 0.0
    for timing in runner.last_timings:
        transformer_known_sec += sum(float(timing.get(key, 0.0) or 0.0) for key in transformer_known_keys)
    transformer_detail = getattr(runner, "last_transformer_detail_timing", {}) or {}
    if isinstance(transformer_detail, dict):
        transformer_known_sec += float(transformer_detail.get("input_contiguous_sec", 0.0) or 0.0)
        transformer_known_sec += float(transformer_detail.get("start_guard_sec", 0.0) or 0.0)
    mask_batch_detail["transformer_known_sec"] = float(transformer_known_sec)
    mask_batch_detail["transformer_outer_gap_sec"] = max(0.0, float(transformer_sec) - float(transformer_known_sec))

    masks = []
    final_norm_timing = None
    mask_timing = None
    with torch.inference_mode():
        if bool(getattr(module, "private_ane_gpu_final_norm_mask", False)):
            mask_outer_started = time.perf_counter()
            try:
                masks, final_norm_timing, mask_timing = _private_ane_mlx_final_norm_mask_many(
                    module,
                    xs,
                    stft_reprs,
                )
                final_norm_stage = "mlx_gpu"
                mask_stage = "mlx_gpu"
            except Exception as exc:
                if not _allow_torch_fallback(module):
                    raise RuntimeError(
                        "private_ane batch MLX GPU final_norm/mask failed and torch fallback is disabled"
                    ) from exc
                module._pymss_private_ane_outer_error = f"final_norm_mask_mlx_gpu: {exc!r}"
                masks, final_norm_timing, mask_timing = _private_ane_torch_final_norm_mask_many(
                    module,
                    xs,
                    stft_reprs,
                    stage="torch_fallback_after_mlx_gpu",
                )
                final_norm_stage = "torch_fp16"
                mask_stage = "torch_fp16"
            mask_batch_detail["mask_outer_sec"] = float(time.perf_counter() - mask_outer_started)
            if isinstance(mask_timing, dict):
                mask_batch_detail["mask_outer_gap_sec"] = max(
                    0.0,
                    float(mask_batch_detail["mask_outer_sec"]) - float(mask_timing.get("wall_sec", 0.0) or 0.0),
                )
            del xs
        else:
            final_norm_stage = "private_ane"
            final_norm_outer_started = time.perf_counter()
            try:
                xs = runner.run_final_norm_tiled_many(xs)
                final_norm_timing = getattr(runner, "last_final_norm_timing", None)
            except Exception as exc:
                if not _allow_torch_fallback(module):
                    raise RuntimeError("private_ane batch final norm failed and torch fallback is disabled") from exc
                module._pymss_private_ane_outer_error = f"final_norm_private_ane: {exc!r}"
                final_norm_stage = "torch_fp16"
                xs_t = [torch.from_numpy(x_np).to(device="cpu", dtype=torch.float16) for x_np in xs]
                norm_started = time.perf_counter()
                xs_t = [module.final_norm(x) for x in xs_t]
                final_norm_timing = {
                    "stage": "torch_fp16",
                    "wall_sec": float(time.perf_counter() - norm_started),
                    "chunks": int(len(xs)),
                }
                xs = [x.detach().cpu().numpy().astype(np.float16, copy=False) for x in xs_t]
            mask_batch_detail["final_norm_outer_sec"] = float(time.perf_counter() - final_norm_outer_started)
            if isinstance(final_norm_timing, dict):
                mask_batch_detail["final_norm_outer_gap_sec"] = max(
                    0.0,
                    float(mask_batch_detail["final_norm_outer_sec"]) - float(final_norm_timing.get("wall_sec", 0.0) or 0.0),
                )

            mask_stage = "private_ane"
            mask_outer_started = time.perf_counter()
            try:
                if bool(getattr(module, "private_ane_fused_mask_estimator", False)):
                    mask_nps = runner.run_mask_estimator_tiled_fused_many(xs)
                    mask_stage = "private_ane_fused"
                else:
                    mask_nps = runner.run_mask_estimator_tiled_many(xs)
                mask_timing = getattr(runner, "last_mask_timing", None)
            except Exception as exc:
                if not _allow_torch_fallback(module):
                    raise RuntimeError("private_ane batch mask estimator failed and torch fallback is disabled") from exc
                module._pymss_private_ane_outer_error = f"mask_private_ane: {exc!r}"
                mask_stage = "torch_fp16"
                mask_started = time.perf_counter()
                mask_nps = []
                for x_np in xs:
                    x = torch.from_numpy(x_np).to(device="cpu", dtype=torch.float16)
                    mask = module._estimate_masks(x)
                    mask_nps.append(mask.detach().cpu().numpy().astype(np.float16, copy=False))
                mask_timing = {
                    "stage": "torch_fp16",
                    "wall_sec": float(time.perf_counter() - mask_started),
                    "chunks": int(len(xs)),
                }
            mask_batch_detail["mask_outer_sec"] = float(time.perf_counter() - mask_outer_started)
            if isinstance(mask_timing, dict):
                mask_batch_detail["mask_outer_gap_sec"] = max(
                    0.0,
                    float(mask_batch_detail["mask_outer_sec"]) - float(mask_timing.get("wall_sec", 0.0) or 0.0),
                )

            del xs
            mask_output_pack_started = time.perf_counter()
            for index, stft_repr in enumerate(stft_reprs):
                mask = torch.from_numpy(mask_nps[index]).to(device="cpu", dtype=torch.float16)
                mask = mask_to_complex_shape(mask, complex_dim=2)
                masks.append(mask.to(device=stft_repr.device, dtype=stft_repr.dtype))
                mask_nps[index] = None
            del mask_nps
            mask_batch_detail["mask_output_pack_sec"] = float(time.perf_counter() - mask_output_pack_started)
    runner.last_final_norm_timing = final_norm_timing
    runner.last_mask_timing = mask_timing

    summary_build_started = time.perf_counter()
    module._pymss_private_ane_last_timings = tuple(runner.last_timings)
    mask_batch_detail["wall_sec"] = float(time.perf_counter() - mask_batch_wall_started)
    module._pymss_private_ane_last_summary = {
        "transformer_sec": float(transformer_sec),
        "gelu_mode": runner._gelu_mode(),
        "fuse_residual": bool(runner._fuse_residual()),
        "fuse_gate_ffn": bool(runner._fuse_gate_ffn()),
        "two_input_gate": bool(runner._two_input_gate()),
        "bridge_pack_gate": bool(runner._bridge_pack_gate()),
        "surface_handoff_gate_ffn": bool(runner._surface_handoff_gate_ffn()),
        "batch_axis_eval": bool(runner._batch_axis_eval()),
        "persistent_transformer_handles": bool(
            getattr(module, "private_ane_persistent_transformer_handles", False)
        ),
        "allow_transformer_handle_cache": bool(
            getattr(module, "private_ane_allow_transformer_handle_cache", False)
        ),
        "tiled_time_attention_pre": bool(runner._tiled_time_attention_pre()),
        "tiled_time_attention_pre_q_chunk": (
            runner._tiled_time_attention_pre_q_chunk() if runner._tiled_time_attention_pre() else 0
        ),
        "fused_band_split": bool(getattr(module, "private_ane_fused_band_split", False)),
        "fused_mask_estimator": bool(getattr(module, "private_ane_fused_mask_estimator", False)),
        "gpu_final_norm_mask": bool(getattr(module, "private_ane_gpu_final_norm_mask", False)),
        "gpu_istft": bool(getattr(module, "private_ane_gpu_istft", False)),
        "torch_fallback_allowed": bool(_allow_torch_fallback(module)),
        "release_aux_handles_before_istft": bool(
            getattr(module, "private_ane_release_aux_handles_before_istft", True)
        ),
        "dynamic_stft": bool(getattr(module, "private_ane_dynamic_stft", False)),
        "outer_stages": f"{band_split_stage}_band_split_{final_norm_stage}_final_norm_{mask_stage}_mask",
        "schedule": "layerwise_many",
        "chunks": len(stft_reprs),
        "band_split": getattr(runner, "last_band_split_timing", None),
        "final_norm": final_norm_timing,
        "mask": mask_timing,
        "mask_batch_detail": mask_batch_detail,
        "transformer_detail": transformer_detail,
        "transformer_timings": tuple(runner.last_timings),
        "memory_samples": tuple(runner.last_memory_samples),
        "bridge_load_cache": {
            "enabled": bool(getattr(runner.bridge, "use_load_cache", False)),
            "hits": int(getattr(runner.bridge, "load_cache_hits", 0)),
            "misses": int(getattr(runner.bridge, "load_cache_misses", 0)),
        },
        "free_profile_by_family": dict(getattr(runner, "_free_profile_by_family", {}) or {}),
        "final_cache_handles": runner.cache_handle_counts(),
    }
    mask_batch_detail["summary_build_sec"] = float(time.perf_counter() - summary_build_started)
    mask_batch_detail["wall_sec"] = float(time.perf_counter() - mask_batch_wall_started)
    return masks


def private_ane_forward_roformer(module, raw_audio: torch.Tensor):
    squeeze_batch = False
    if raw_audio.ndim == 2:
        chunk = raw_audio
        squeeze_batch = True
    elif raw_audio.ndim == 3 and raw_audio.shape[0] == 1:
        chunk = raw_audio[0]
    else:
        raise NotImplementedError("private_ane forward currently supports a single stereo chunk only")
    stft_repr, context = private_ane_stft_roformer(module, chunk)
    runner = _runner(module)
    preserve_stft_handles = bool(
        hasattr(runner, "preserve_stft_handles_between_batches")
        and runner.preserve_stft_handles_between_batches()
    )
    if hasattr(runner, "clear_stft_cache") and not preserve_stft_handles:
        runner.clear_stft_cache()
    mask = private_ane_forward_mask_core(module, stft_repr)
    if bool(getattr(module, "private_ane_release_aux_handles_before_istft", True)):
        runner = getattr(module, "_private_ane_runner", None)
        if runner is not None and hasattr(runner, "clear_aux_handle_cache"):
            runner.clear_aux_handle_cache()
    stft_complex = torch.view_as_complex(stft_repr.unsqueeze(1).contiguous())
    mask_complex = torch.view_as_complex(mask.contiguous()).type(stft_complex.dtype)
    output = private_ane_istft_roformer(module, stft_complex * mask_complex, context, context.audio_length)
    if hasattr(runner, "clear_irfft_cache"):
        runner.clear_irfft_cache()
    summary = dict(getattr(module, "_pymss_private_ane_last_summary", {}) or {})
    summary["forward_path"] = "private_ane_end_to_end"
    if not preserve_stft_handles:
        summary["stft_cache_releases"] = int(summary.get("stft_cache_releases", 0) or 0) + 1
    summary["irfft_cache_releases"] = int(summary.get("irfft_cache_releases", 0) or 0) + 1
    summary["persistent_stft_handles"] = bool(preserve_stft_handles)
    summary["dynamic_stft"] = bool(getattr(module, "private_ane_dynamic_stft", False))
    summary["preload_stft_handles"] = bool(
        hasattr(runner, "_preload_stft_handles") and runner._preload_stft_handles()
    )
    summary["stft_preload"] = getattr(runner, "last_stft_preload_timing", None)
    summary["stft"] = getattr(module, "_pymss_private_ane_last_stft", {}) or {}
    summary["istft"] = getattr(module, "_pymss_private_ane_last_istft", {}) or {}
    module._pymss_private_ane_last_summary = summary
    return output[0] if squeeze_batch else output
