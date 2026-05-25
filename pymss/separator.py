import gc
import os
import logging
import re
from contextlib import contextmanager, nullcontext
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import torch
import numpy as np
import platform
import subprocess
from time import time
from tqdm import tqdm

from .audio_io import load_audio, save_audio
from .utils import demix, get_model_from_config
from .logger import get_separation_logger, set_log_level
from .config import AttrDict


INFERENCE_PARAM_TARGETS = {
    'batch_size': 'inference',
    'overlap_size': 'inference',
    'chunk_size': 'audio',
    'normalize': 'inference',
    'mask_mode': 'inference',
    'window_size': 'inference',
    'aggression': 'inference',
    'enable_tta': 'inference',
    'enable_post_process': 'inference',
    'post_process_threshold': 'inference',
    'high_end_process': 'inference',
    'use_amp': 'inference',
    'cuda_attention_backend': 'inference',
    'mps_attention_backend': 'inference',
    'mps_mlx_min_tokens': 'inference',
    'mps_model_backend': 'inference',
    'mps_model_compute_dtype': 'inference',
    'fuse_conv_bn': 'inference',
    'use_channels_last': 'inference',
    'shifts': 'inference',
    'split': 'inference',
    'overlap': 'inference',
    'stem_batch_size': 'inference',
}
PASSTHROUGH_INFERENCE_PARAMS = frozenset({
    'normalize',
    'mask_mode',
    'enable_tta',
    'enable_post_process',
    'high_end_process',
    'use_amp',
    'cuda_attention_backend',
    'mps_attention_backend',
    'mps_model_backend',
    'mps_model_compute_dtype',
    'fuse_conv_bn',
    'use_channels_last',
    'split',
})
FAST_INIT_MODEL_TYPES = {'bs_roformer', 'bs_roformer_hyperace', 'mel_band_roformer'}
LEGACY_DEMUCS_MODEL_TYPES = {'demucs', 'tasnet', 'legacy_demucs', 'legacy_tasnet'}


def _select_device(device, device_ids, logger):
    if device not in ['cpu', 'cuda', 'mps']:
        if torch.cuda.is_available():
            logger.debug("CUDA is available in Torch, setting Torch device to CUDA")
            return f'cuda:{device_ids[0]}'
        if torch.backends.mps.is_available():
            logger.debug("Apple Silicon MPS/CoreML is available in Torch, setting Torch device to MPS")
            return "mps"
        return "cpu"

    if device == "cpu":
        logger.warning("No hardware acceleration could be configured, running in CPU mode")
    return device


def _unwrap_state_dict(state_dict):
    for key in ('state', 'state_dict', 'model_state_dict'):
        if key in state_dict:
            return state_dict[key]
    return state_dict


def _apollo_state_dict_path(model_path):
    root, ext = os.path.splitext(model_path)
    candidates = []
    if ext:
        candidates.append(f"{root}.pymss_state_dict.pt")
    candidates.append(f"{model_path}.pymss_state_dict.pt")
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return model_path


def _load_state_dict(model_type, model_path, device):
    if model_type == 'vr':
        return None
    map_location = "cpu"
    if model_type == 'htdemucs':
        stubbed_modules = _install_demucs_pickle_stubs()
        try:
            state_dict = torch.load(model_path, map_location=map_location, weights_only=False)
        finally:
            _restore_modules(stubbed_modules)
        return _unwrap_state_dict(state_dict)
    if model_type == 'apollo':
        model_path = _apollo_state_dict_path(model_path)
        return _unwrap_state_dict(torch.load(model_path, map_location=map_location, weights_only=False))
    try:
        return _unwrap_state_dict(torch.load(model_path, map_location=map_location, weights_only=True, mmap=True))
    except (TypeError, ValueError, RuntimeError):
        return _unwrap_state_dict(torch.load(model_path, map_location=map_location, weights_only=True))


@contextmanager
def _skip_torch_default_init():
    classes = (
        torch.nn.Linear,
        torch.nn.Bilinear,
        torch.nn.Conv1d,
        torch.nn.Conv2d,
        torch.nn.Conv3d,
        torch.nn.ConvTranspose1d,
        torch.nn.ConvTranspose2d,
        torch.nn.ConvTranspose3d,
        torch.nn.BatchNorm1d,
        torch.nn.BatchNorm2d,
        torch.nn.BatchNorm3d,
        torch.nn.InstanceNorm1d,
        torch.nn.InstanceNorm2d,
        torch.nn.InstanceNorm3d,
        torch.nn.LayerNorm,
        torch.nn.GroupNorm,
        torch.nn.Embedding,
        torch.nn.EmbeddingBag,
        torch.nn.RNN,
        torch.nn.GRU,
        torch.nn.LSTM,
        torch.nn.MultiheadAttention,
    )
    saved = {cls: cls.reset_parameters for cls in classes if hasattr(cls, 'reset_parameters')}
    try:
        for cls in saved:
            cls.reset_parameters = lambda self: None
        yield
    finally:
        for cls, reset_parameters in saved.items():
            cls.reset_parameters = reset_parameters


def _install_demucs_pickle_stubs():
    import sys
    import types

    module_names = ('demucs', 'demucs.demucs', 'demucs.hdemucs', 'demucs.htdemucs')
    previous = {name: sys.modules.get(name) for name in module_names}
    package = sys.modules.setdefault('demucs', types.ModuleType('demucs'))
    package.__path__ = []
    for module_name, class_names in {
        'demucs': ('Demucs',),
        'hdemucs': ('HDemucs', 'HTDemucs'),
        'htdemucs': ('HTDemucs',),
    }.items():
        full_name = f'demucs.{module_name}'
        module = sys.modules.setdefault(full_name, types.ModuleType(full_name))
        setattr(package, module_name, module)
        for class_name in class_names:
            if not hasattr(module, class_name):
                setattr(module, class_name, type(class_name, (), {'__module__': full_name}))
    return previous


def _restore_modules(previous):
    import sys

    for name, module in previous.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def _runtime_model_type(model_type, state_dict):
    return 'bs_roformer_hyperace' if model_type == 'bs_roformer' and any('.segm.' in key for key in state_dict) else model_type


def _infer_mel_band_roformer_mlp_hidden_layers(state_dict):
    pattern = re.compile(r'(?:^|\.)mask_estimators\.0\.to_freqs\.0\.0\.(\d+)\.weight$')
    layer_indices = sorted({int(match.group(1)) for key in state_dict for match in [pattern.search(key)] if match})
    if not layer_indices:
        return None
    return len(layer_indices) - 1


def _store_torch_model_on_cpu_for_mlx(config, device):
    return (
        torch.device(device).type == "mps"
        and config.inference.get("mps_model_backend", "torch") == "mlx_full"
    )


def _coerce_mps_float64(module):
    for child in module.modules():
        for name, param in list(child._parameters.items()):
            if param is not None and param.dtype == torch.float64:
                child._parameters[name] = torch.nn.Parameter(param.detach().float(), requires_grad=param.requires_grad)
        for name, buffer in list(child._buffers.items()):
            if buffer is not None and buffer.dtype == torch.float64:
                child._buffers[name] = buffer.float()


def _model_is_stereo(model_type, config):
    if model_type == 'vr':
        return True
    if model_type in ['bs_roformer', 'bs_roformer_hyperace', 'mel_band_roformer', *LEGACY_DEMUCS_MODEL_TYPES]:
        return config.model.get("stereo", True)
    return True


def _prepare_mix_channels(mix, is_stereo, logger):
    if is_stereo and len(mix.shape) == 1:
        logger.warning("Track is mono, but model is stereo, adding a second channel.")
        return np.stack([mix, mix], axis=0)
    if is_stereo and len(mix.shape) > 2:
        logger.warning("Track has more than 2 channels, taking mean of all channels and adding a second channel.")
        mono = np.mean(mix, axis=0)
        return np.stack([mono, mono], axis=0)
    if not is_stereo and len(mix.shape) != 1:
        logger.warning("Track has more than 1 channels, but model is mono, taking mean of all channels.")
        return np.mean(mix, axis=0)
    return mix


def _normalize_mix(mix, enabled, logger):
    if not enabled:
        return mix, None

    mono = mix.mean(0)
    mean = mono.mean()
    std = mono.std()
    logger.debug(f"Normalize mix with mean: {mean}, std: {std}")
    return (mix - mean) / std, (mean, std)


def _denormalize(estimates, stats):
    return estimates if stats is None else estimates * stats[1] + stats[0]


def _tta_variants(mix, use_tta, logger):
    if not use_tta:
        return [mix.copy()]
    variants = [mix.copy(), mix[::-1].copy(), -1. * mix.copy()]
    logger.debug(f"User needs to apply TTA, total tracks: {len(variants)}")
    return variants


def _merge_tta_results(results):
    waveforms = results[0]
    for index, result in enumerate(results[1:], start=1):
        for stem, audio in result.items():
            waveforms[stem] += audio[::-1].copy() if index == 1 else -1.0 * audio

    for stem in waveforms:
        waveforms[stem] /= len(results)
    return waveforms


def _build_results(waveforms, instruments, mix_orig, config, norm_stats, logger):
    target_instrument = config.training.target_instrument
    if target_instrument is None:
        return {
            instr: _denormalize(waveforms[instr].T, norm_stats)
            for instr in instruments
        }

    results = {}
    if target_instrument in instruments:
        results[target_instrument] = _denormalize(waveforms[target_instrument].T, norm_stats)
    other_instruments = [instr for instr in config.training.instruments if instr != target_instrument]
    logger.debug(f"target_instrument is not null, extracting instrumental from {target_instrument}, other_instruments: {other_instruments}")
    if other_instruments:
        secondary = other_instruments[0]
        if secondary in instruments:
            waveforms[secondary] = mix_orig - waveforms[target_instrument]
            results[secondary] = _denormalize(waveforms[secondary].T, norm_stats)
    return results


def _resolve_instruments(config, stems=None):
    instruments = config.training.instruments.copy()
    if stems is None:
        source_indices = None if config.training.target_instrument is None else (0,)
        return instruments, source_indices

    stem_list = [stems] if isinstance(stems, str) else list(stems)
    lower_to_index = {instr.lower(): index for index, instr in enumerate(instruments)}
    selected, indices = [], []
    for stem in stem_list:
        key = stem.lower()
        if key not in lower_to_index:
            raise ValueError(f"Invalid instrument key: {stem}. Valid instrument keys: {instruments}")
        index = lower_to_index[key]
        if index in indices:
            continue
        selected.append(instruments[index])
        indices.append(index)
    if not selected:
        raise ValueError("stems must not be empty")
    source_indices = tuple(indices) if config.training.target_instrument is None else (0,)
    return selected, source_indices


def _get_store_dir(store_dirs, instr):
    if instr in store_dirs:
        return store_dirs[instr]
    instr_lower = instr.lower()
    for key, value in store_dirs.items():
        if key.lower() == instr_lower:
            return value
    return ""


class MSSeparator:
    def __init__(
            self,
            model_type,
            model_path,
            config_path = None,
            device = 'auto',
            device_ids = [0],
            output_format = 'wav',
            use_tta = False,
            store_dirs = 'results', # str for single folder, dict with instrument keys for multiple folders
            audio_params = {"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2},
            logger = get_separation_logger(),
            debug = False,
            inference_params = {
                "batch_size": None,
                "overlap_size": None,
                "chunk_size": None,
                "normalize": None,
                "mask_mode": None,
            }
    ):

        if not model_type:
            raise ValueError('model_type is required')
        if not model_path:
            raise ValueError('model_path is required')

        self.model_type = model_type

        self.model_path = model_path
        self.config_path_given = config_path is not None
        self.config_path = config_path if config_path else (model_path + '.yaml')
        self.output_format = output_format
        self.use_tta = use_tta
        self.store_dirs = store_dirs
        self.audio_params = audio_params
        self.logger = logger
        self.debug = debug
        self.inference_params = inference_params

        if self.debug:
            set_log_level(logger, logging.DEBUG)
        else:
            set_log_level(logger, logging.INFO)

        self.log_system_info()
        self.check_ffmpeg_installed()

        self.device_ids = device_ids
        self.device = _select_device(device, self.device_ids, self.logger)

        torch.backends.cudnn.benchmark = True
        self.logger.info(f'Using device: {self.device}, device_ids: {self.device_ids}')

        self.model, self.config = self.load_model()

        if type(self.store_dirs) == str:
            self.store_dirs = {k: self.store_dirs for k in self.config.training.instruments}

        valid_instruments = {instr.lower() for instr in self.config.training.instruments}
        for key in list(self.store_dirs.keys()):
            if key not in self.config.training.instruments and key.lower() not in valid_instruments:
                self.store_dirs.pop(key)
                self.logger.warning(f"Invalid instrument key: {key}, removing from store_dirs")
                self.logger.warning(f"Valid instrument keys: {self.config.training.instruments}")

    @classmethod
    def from_model_name(cls, model_name, model_dir=None, download=False, source="modelscope", endpoint=None, **kwargs):
        if download:
            from .model_download import download_model

            download_model(model_name, model_dir=model_dir, source=source, endpoint=endpoint)

        from .model_registry import resolve_model

        resolved = resolve_model(model_name, model_dir=model_dir, require_supported=True, require_exists=True)
        return cls(
            model_type=resolved["model_type"],
            model_path=resolved["model_path"],
            config_path=resolved["config_path"],
            **kwargs,
        )

    def log_system_info(self):
        os_name = platform.system()
        os_version = platform.version()
        self.logger.debug(f"Operating System: {os_name} {os_version}")

        python_version = platform.python_version()
        self.logger.debug(f"Python Version: {python_version}")

        pytorch_version = torch.__version__
        self.logger.debug(f"PyTorch Version: {pytorch_version}")

    def check_ffmpeg_installed(self):
        try:
            ffmpeg_version_output = subprocess.check_output(["ffmpeg", "-version"], text=True)
            first_line = ffmpeg_version_output.splitlines()[0]
            self.logger.debug(f"FFmpeg installed: {first_line}")
        except FileNotFoundError:
            self.logger.warning("FFmpeg is not installed. Please install FFmpeg to use this package.")

    def load_model(self):
        start_time = time()
        if self.model_type == 'vr':
            from .modules.vocal_remover.vr_models import get_vr_model_metadata
            from .modules.vocal_remover import VRSeparator

            model_data = get_vr_model_metadata(self.model_path)
            instruments = [model_data["primary_stem"], model_data["secondary_stem"]]
            config = AttrDict({
                "training": {
                    "instruments": instruments,
                    "target_instrument": None,
                    "use_amp": True,
                },
                "audio": {
                    "sample_rate": 44100,
                },
                "inference": {
                    "batch_size": 2,
                    "window_size": 512,
                    "aggression": 5,
                    "enable_tta": self.use_tta,
                    "enable_post_process": False,
                    "post_process_threshold": 0.2,
                    "high_end_process": False,
                    "use_amp": True,
                    "fuse_conv_bn": False,
                    "use_channels_last": False,
                    "normalize": False,
                },
            })
            self.update_inference_params(config, self.inference_params)
            common_config = {
                "logger": self.logger,
                "debug": self.debug,
                "torch_device": self.device,
                "torch_device_cpu": torch.device("cpu"),
                "torch_device_mps": torch.device("mps") if torch.device(self.device).type == "mps" else None,
                "model_name": os.path.basename(self.model_path),
                "model_path": self.model_path,
                "model_data": model_data,
                "sample_rate": 44100,
                "callback": None,
            }
            model = VRSeparator(common_config, config.inference)
            model.load_model()
            self.logger.info(f"Separator params: model_type: vr, model_path: {self.model_path}, output_folder: {self.store_dirs}")
            self.logger.info(f"Audio params: output_format: {self.output_format}, audio_params: {self.audio_params}")
            self.logger.info(f"Model params: instruments: {config.training.instruments}, target_instrument: None")
            self.logger.debug(f"Loading VR model completed, duration: {time() - start_time:.2f} seconds")
            return model, config

        if self.model_type in LEGACY_DEMUCS_MODEL_TYPES:
            from .modules.legacy_demucs import load_legacy_demucs_model

            config_path = self.config_path if self.config_path_given else None
            model, config = load_legacy_demucs_model(self.model_path, config_path)
            config = AttrDict(config)
            self.update_inference_params(config, self.inference_params)
            model = model.to(self.device)
            model.eval()

            self.logger.info(f"Separator params: model_type: {self.model_type}, model_path: {self.model_path}, config_path: {config_path}, output_folder: {self.store_dirs}")
            self.logger.info(f"Audio params: output_format: {self.output_format}, audio_params: {self.audio_params}")
            self.logger.info(f"Model params: instruments: {config.training.get('instruments', None)}, target_instrument: {config.training.get('target_instrument', None)}")
            self.logger.debug(f"Model params: batch_size: {config.inference.get('batch_size', None)}, overlap_size: {config.inference.get('overlap_size', None)}, chunk_size: {config.audio.get('chunk_size', None)}, normalize: {config.inference.get('normalize', None)}, use_tta: {self.use_tta}")
            self.logger.debug(f"Loading legacy Demucs/TasNet model completed, duration: {time() - start_time:.2f} seconds")
            return model, config

        state_dict = _load_state_dict(self.model_type, self.model_path, self.device)
        model_type = _runtime_model_type(self.model_type, state_dict)
        model_kwargs_override = None
        if model_type == 'mel_band_roformer':
            model_kwargs_override = {
                'mlp_hidden_layers': _infer_mel_band_roformer_mlp_hidden_layers(state_dict),
            }

        init_context = _skip_torch_default_init() if model_type in FAST_INIT_MODEL_TYPES else nullcontext()
        with init_context:
            model, config = get_model_from_config(model_type, self.config_path, model_kwargs_override=model_kwargs_override)

        self.update_inference_params(config, self.inference_params)
        self.apply_model_inference_config(model, config)

        self.logger.info(f"Separator params: model_type: {model_type}, model_path: {self.model_path}, config_path: {self.config_path}, output_folder: {self.store_dirs}")
        self.logger.info(f"Audio params: output_format: {self.output_format}, audio_params: {self.audio_params}")
        self.logger.info(f"Model params: instruments: {config.training.get('instruments', None)}, target_instrument: {config.training.get('target_instrument', None)}")
        self.logger.debug(f"Model params: batch_size: {config.inference.get('batch_size', None)}, overlap_size: {config.inference.get('overlap_size', None)}, chunk_size: {config.audio.get('chunk_size', None)}, normalize: {config.inference.get('normalize', None)}, use_tta: {self.use_tta}")

        try:
            model.load_state_dict(state_dict, assign=True)
        except TypeError:
            model.load_state_dict(state_dict)
        if torch.device(self.device).type == "mps":
            _coerce_mps_float64(model)

        keep_torch_model_cpu = _store_torch_model_on_cpu_for_mlx(config, self.device)
        if len(self.device_ids) > 1 and not keep_torch_model_cpu:
            model = torch.nn.DataParallel(model, device_ids=self.device_ids)
        model = model.to("cpu" if keep_torch_model_cpu else self.device)
        model.eval()

        self.logger.debug(f"Loading model completed, duration: {time() - start_time:.2f} seconds")
        return model, config

    def apply_model_inference_config(self, model, config):
        if hasattr(model, 'set_mask_mode'):
            model.set_mask_mode(config.inference.get('mask_mode', 'no_segm'))
        cuda_attention_backend = config.inference.get('cuda_attention_backend', None)
        if cuda_attention_backend is not None:
            for module in model.modules():
                if hasattr(module, 'set_cuda_attention_backend'):
                    module.set_cuda_attention_backend(cuda_attention_backend)
        model_backend = config.inference.get('mps_model_backend', None)
        if model_backend is not None:
            compute_dtype = config.inference.get('mps_model_compute_dtype', None)
            for module in model.modules():
                if hasattr(module, 'set_mps_model_backend'):
                    module.set_mps_model_backend(model_backend, compute_dtype)
        backend = config.inference.get('mps_attention_backend', None)
        min_tokens = config.inference.get('mps_mlx_min_tokens', 128)
        if backend is not None:
            for module in model.modules():
                if hasattr(module, 'set_mps_attention_backend'):
                    module.set_mps_attention_backend(backend, min_tokens)

    def update_inference_params(self, config, params):
        for key, section in INFERENCE_PARAM_TARGETS.items():
            value = params.get(key)
            if value is None:
                continue
            if key not in PASSTHROUGH_INFERENCE_PARAMS:
                value = float(value) if key in {'post_process_threshold', 'overlap'} else int(value)
            config[section][key] = value
        return config

    def _save_output(self, instr, audio, sr, file_name, save_dir):
        output_format = self.output_format.lower()
        os.makedirs(save_dir, exist_ok=True)
        self.save_audio(audio, sr, f"{file_name}_{instr}", save_dir)
        self.logger.debug(f"Saved {instr} for {file_name}_{instr}.{output_format} in {save_dir}")

    def _wait_save_futures(self, path, futures):
        save_ok = True
        for future in futures:
            try:
                future.result()
            except Exception as e:
                save_ok = False
                self.logger.warning(f'Cannot save track: {path}, error: {str(e)}')
        return save_ok

    @staticmethod
    def _submit_load(load_executor, paths, index, sample_rate):
        return None if index >= len(paths) else load_executor.submit(load_audio, paths[index], sr=sample_rate, mono=False)

    def _submit_save_outputs(self, save_executor, results, sr, file_name):
        return [
            save_executor.submit(self._save_output, instr, audio, sr, file_name, output_dir)
            for instr, audio in results.items()
            for save_dir in [_get_store_dir(self.store_dirs, instr)]
            if save_dir
            for output_dir in (save_dir if isinstance(save_dir, list) else [save_dir])
        ]

    def _stems_to_save(self):
        stems = [
            instr
            for instr in self.config.training.instruments
            if _get_store_dir(self.store_dirs, instr)
        ]
        return stems or None

    def _stem_batches_to_save(self):
        stems = self._stems_to_save()
        if stems is None:
            return [None]
        batch_size = int(self.config.inference.get('stem_batch_size', 0))
        if batch_size <= 0 or len(stems) <= batch_size:
            return [stems]
        return [stems[index:index + batch_size] for index in range(0, len(stems), batch_size)]

    def _drain_save_queue(self, pending_saves, success_files, progress, max_pending_saves=0, record_success=True):
        ok = True
        while len(pending_saves) > max_pending_saves:
            saved_path, saved_futures = pending_saves.popleft()
            saved_ok = self._wait_save_futures(saved_path, saved_futures)
            ok = saved_ok and ok
            if saved_ok and record_success:
                success_files.append(os.path.basename(saved_path))
                if progress is not None:
                    progress.update(1)
        return ok

    def _wait_pending_saves(self, pending_saves):
        ok = True
        while pending_saves:
            saved_path, saved_futures = pending_saves.popleft()
            ok = self._wait_save_futures(saved_path, saved_futures) and ok
        return ok

    def process_folder(self, input_folder):
        if not os.path.isdir(input_folder):
            raise ValueError(f"Input folder '{input_folder}' does not exist.")

        all_mixtures_path = [os.path.join(input_folder, f) for f in os.listdir(input_folder)]
        if not all_mixtures_path:
            return []

        sample_rate = 44100
        if 'sample_rate' in self.config.audio:
            sample_rate = self.config.audio['sample_rate']
        self.logger.info(f"Input_folder: {input_folder}, Total files found: {len(all_mixtures_path)}, Use sample rate: {sample_rate}")

        success_files, pending_saves = [], deque()
        max_pending_saves = 12

        progress = tqdm(all_mixtures_path, desc="Total progress") if not self.debug else None
        try:
            with (
                ThreadPoolExecutor(max_workers=1, thread_name_prefix="pymss-load") as load_executor,
                ThreadPoolExecutor(max_workers=2, thread_name_prefix="pymss-save") as save_executor,
            ):
                load_future = self._submit_load(load_executor, all_mixtures_path, 0, sample_rate)

                for index, path in enumerate(all_mixtures_path):
                    if progress is not None:
                        progress.set_postfix({'track': os.path.basename(path)})

                    try:
                        mix, sr = load_future.result()
                    except Exception as e:
                        self.logger.warning(f'Cannot process track: {path}, error: {str(e)}')
                        load_future = self._submit_load(load_executor, all_mixtures_path, index + 1, sample_rate)
                        continue

                    load_future = self._submit_load(load_executor, all_mixtures_path, index + 1, sample_rate)

                    self.logger.debug(f"Starting separation process for audio_file: {path}")
                    try:
                        file_name, _ = os.path.splitext(os.path.basename(path))
                        track_saves = deque()
                        save_ok = True
                        for stems in self._stem_batches_to_save():
                            results = self.separate(mix, pbar=False, stems=stems)
                            track_saves.append((path, self._submit_save_outputs(save_executor, results, sr, file_name)))
                            save_ok = self._drain_save_queue(
                                track_saves, success_files, None, 1, record_success=False
                            ) and save_ok
                            del results
                        save_ok = self._wait_pending_saves(track_saves) and save_ok
                    except Exception as e:
                        self.logger.warning(f'Cannot separate track: {path}, error: {str(e)}')
                        del mix
                        continue

                    self.logger.debug(f"Separation audio_file: {path} completed. Starting to save results.")
                    if save_ok:
                        success_files.append(os.path.basename(path))
                        if progress is not None:
                            progress.update(1)

                    del mix

                self._drain_save_queue(pending_saves, success_files, progress)
        finally:
            if progress is not None:
                progress.close()
        return success_files

    def separate(self, mix, pbar=True, stems=None):
        return self._separate(mix, pbar=pbar, stems=stems)

    def _separate(self, mix, pbar, stems=None):
        mix = _prepare_mix_channels(mix, _model_is_stereo(self.model_type, self.config), self.logger)
        if self.model_type == 'vr':
            return self.model.separate_array(mix, self.config.audio.get('sample_rate', 44100))

        instruments, source_indices = _resolve_instruments(self.config, stems)
        if self.config.training.target_instrument is not None:
            self.logger.debug("Target instrument is not null, set primary_stem to target_instrument, secondary_stem will be calculated by mix - target_instrument")

        mix_orig = mix.copy()
        mix, norm_stats = _normalize_mix(mix, self.config.inference.get('normalize', False), self.logger)
        full_result = [
            demix(self.config, self.model, track, self.device, pbar=pbar, model_type=self.model_type, source_indices=source_indices)
            for track in _tta_variants(mix, self.use_tta, self.logger)
        ]

        self.logger.debug("Finished demixing tracks.")
        waveforms = _merge_tta_results(full_result)
        self.logger.debug(f"Starting to extract waveforms for instruments: {instruments}")
        results = _build_results(waveforms, instruments, mix_orig, self.config, norm_stats, self.logger)
        self.logger.debug("Separation process completed.")
        return results

    def save_audio(self, audio, sr, file_name, store_dir):
        output_format = self.output_format.lower()
        file = os.path.join(store_dir, f"{file_name}.{output_format}")
        save_audio(file, audio, sr, output_format, self.audio_params)

    def del_cache(self):
        self.logger.debug("Running garbage collection...")
        gc.collect()
        if "mps" in self.device:
            self.logger.debug("Clearing MPS cache...")
            torch.mps.empty_cache()
        if "cuda" in self.device:
            self.logger.debug("Clearing CUDA cache...")
            torch.cuda.empty_cache()
