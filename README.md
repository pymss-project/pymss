# pymss

Python package for music source separation. <br>
[English]   [简体中文](./README_CN.md)

## Install

Example of using pip to install `pymss` package：

```sh
pip install pymss
```

## Usage

### CLI inference

Run inference by catalog model name. If the model, config, or auxiliary files are missing locally, the CLI downloads them automatically before inference.

```sh
pymss infer bs_roformer_voc_hyperacev2 \
  -i path/to/input_folder \
  -o results \
  --device auto \
  --format wav
```

The default download source is ModelScope. You can choose another source or model directory:

```sh
pymss --model-dir /path/to/models infer bs_roformer_voc_hyperacev2 \
  --source hf-mirror \
  -i path/to/input_folder \
  -o results
```

When running from a source checkout without installation, use `python -m pymss.cli` instead of `pymss`.

### Python API

Use a catalog model name directly. You do not need to pass `model_type`, `model_path`, or `config_path`.

```python
from pymss import MSSeparator

separator = MSSeparator.from_model_name(
    "bs_roformer_voc_hyperacev2",
    download=True,
    device="auto",
    output_format="wav",
    store_dirs="results",
)
separator.process_folder("path/to/input_folder")
```

`download=True` downloads missing model files before loading. Omit it for strict local-only loading.

### Manual model paths

Use the full constructor for custom weights that are not in the model catalog.

```python
from pymss import MSSeparator, get_separation_logger

# init
separator = MSSeparator(
    model_type='htdemucs', 
    model_path='path/to/model',
    config_path='path/to/config',
    device='cuda',
    device_ids=[0],
    output_format='wav',
    use_tta=True,
    store_dirs={
        "vocals": "./output/vocals",
        "other": None # None or missing this stem will result in no output file for this stem. This example will output the vocal's stem in ./output/vocals and ignoring the other(instrumental) stem. Making sure the key(s) match the config file.
    },
    audio_params={"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}, # Can be omitted
    logger=get_separation_logger(), # Can be omitted
    debug=False, # Can be omitted
    inference_params={
        "batch_size": 4,
        "overlap_size": 512,
        "chunk_size": 1024,
        "normalize": True
    } # Can be omitted
)

# process all audio files in the folder
separator.process_folder('path/to/input_folder')
```

### Manual Constructor Parameters

- model_type: The type of model, e.g., 'htdemucs'. Must be one of 
    ['bs_roformer', 
    'mel_band_roformer', 
    'htdemucs', 
    'mdx23c', 
    'bandit', 
    'bandit_v2', 
    'scnet', 
    'apollo',
    'vr']
- model_path: The path to the model file.
- config_path: The path to the configuration file.
- device: The type of device, default is 'auto'. Must be one of ['auto', 'cuda', 'mps', 'cpu']
- device_ids: List of device IDs, default is [0].
- output_format: The output audio format, default is 'wav'. Must be one of ['wav', 'flac', 'mp3', 'm4a']
- use_tta: Whether to use TTA, default is False. Using TTA will triple the processing time with a little bit improvement in quality.
- store_dirs: Storage directories, can be a single folder path or a dictionary with instrument keys.
- audio_params: Audio parameters including wav_bit_depth, flac_bit_depth, mp3_bit_rate, m4a_bit_rate, and m4a_aac_at_quality. Default is {"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}.
- logger: Logger instance. Default is pymss.get_separation_logger()
- debug: Whether to enable debug mode, default is False.
- inference_params: Inference parameters including batch_size, overlap_size, chunk_size, normalize, and `cuda_attention_backend`. Default is all None (means all params are depended on the config file). For `model_type='vr'`, supported keys are `batch_size`, `window_size`, `aggression`, `enable_tta`, `enable_post_process`, `post_process_threshold`, and `high_end_process`.

### CUDA Attention Backend

RoFormer-family models default to cuDNN attention on CUDA when the installed PyTorch build exposes it, otherwise they use PyTorch's default SDPA path. Override with `inference_params={"cuda_attention_backend": "auto"}` if you want fallback probing. Valid values are `auto`, `default`, `flash`, `cudnn`, `efficient`, `math`, and `xformers`. `auto` tries cuDNN attention first, then PyTorch memory-efficient SDPA, then PyTorch default SDPA. `xformers` is optional and only used if installed locally; it is not a required dependency.

### Apple Silicon MLX Backend

On `device='mps'`, an optional full MLX forward path can be enabled explicitly:

```python
inference_params={
    "mps_model_backend": "mlx_full",
    "mps_model_compute_dtype": "float16",
}
```

On Apple Silicon, `setup.py` installs `mlx>=0.31.0` for this backend. The default path remains Torch. If MLX is missing or a non-VR backend fails, the model records `_pymss_mlx_full_backend_error` and falls back to Torch.

### Model Compatibility

HTDemucs checkpoints whose config uses `model: htdemucs` and `htdemucs.cac: true` are supported through `model_type='htdemucs'`.

Legacy Demucs/TasNet `.th` weights can use `model_type='legacy_demucs'` or `model_type='legacy_tasnet'` without a MSST YAML config. The dependency-free legacy loader supports classic Demucs, v3 time-domain Demucs, ConvTasNet, CaC HDemucs, package-style HTDemucs, multi-frequency CaC HDemucs, and simple Demucs bag YAML files. DiffQ-quantized checkpoints and non-CaC/Wiener HDemucs still need a dedicated legacy loader.

UVR VR support is available for the supported UVR/VR series `.pth` weights. Use the catalog model name in the same CLI/API paths as other models. The output stems are read from the built-in VR model list, for example `Vocals`, `Instrumental`, `No Echo`, or `Echo`.

```sh
pymss infer 1_HP-UVR \
  -i path/to/input_folder \
  -o results \
  --device auto \
  --param batch_size=2 \
  --param window_size=512 \
  --param aggression=5
```

```python
separator = MSSeparator.from_model_name(
    "1_HP-UVR",
    download=True,
    device="auto",
    output_format="wav",
    store_dirs="results",
    inference_params={
        "batch_size": 2,
        "window_size": 512,
        "aggression": 5,
    },
)
separator.process_folder("path/to/input_folder")
```

### Hugging Face Configs

Some model configs downloaded from Hugging Face or MSST-WebUI use `inference.num_overlap`. This optimized pymss path uses `inference.overlap_size` instead. If the config only has `num_overlap`, add an explicit `overlap_size` or pass it through `inference_params`; otherwise pymss falls back to 50% overlap and inference will be much slower.

Recommended fast setting:

```yaml
audio:
  chunk_size: 480000
inference:
  batch_size: 2
  overlap_size: 24000  # 5% of chunk_size
```

### RTX 5090 Benchmark

Measured on an NVIDIA GeForce RTX 5090 with PyTorch 2.9.1+cu128, CUDA 12.8, no TTA, one warmup and three measured runs.

| model | type | RTFx | 1-hour audio |
|---|---|---:|---:|
| BS-Roformer-HyperACE_v2_voc | bs_roformer | 231.83x | 15.5s |
| model_bs_roformer_ep_368_sdr_12.9628 | bs_roformer | 109.06x | 33.0s |
| logic_bs_roformer | bs_roformer | 159.71x | 22.5s |
| mel-band-roformer-deux | mel_band_roformer | 169.93x | 21.2s |
| Mel-Band-Roformer-big | mel_band_roformer | 194.05x | 18.6s |
| model_vocals_mdx23c_sdr_10.17 | mdx23c | 209.41x | 17.2s |
| HTDemucs4 | htdemucs | 200.52x | 18.0s |
| scnet_checkpoint_musdb18 | scnet | 356.85x | 10.1s |
| model_bandit_plus_dnr_sdr_11.47 | bandit | 122.76x | 29.3s |
| checkpoint-multi_state_dict | bandit_v2 | 112.33x | 32.0s |
| Apollo_LQ_MP3_restoration | apollo | 100.62x | 35.8s |

VR models were measured with `batch_size=2`, `window_size=512`, `aggression=5`, TTA off, post-processing off.

| VR model | RTFx | 1-hour audio |
|---|---:|---:|
| UVR-DeNoise-Lite | 243.62x | 14.8s |
| Harmonic_Noise_Separation_yxlllc | 221.22x | 16.3s |
| MGM_HIGHEND_v4 | 217.39x | 16.6s |
| MGM_LOWEND_A_v4 | 133.67x | 26.9s |
| MGM_MAIN_v4 | 118.56x | 30.4s |
| 11_SP-UVR-2B-32000-2 | 109.73x | 32.8s |
| 10_SP-UVR-2B-32000-1 | 109.03x | 33.0s |
| 12_SP-UVR-3B-44100 | 104.67x | 34.4s |
| MGM_LOWEND_B_v4 | 100.64x | 35.8s |
| 15_SP-UVR-MID-44100-1 | 99.00x | 36.4s |
| 16_SP-UVR-MID-44100-2 | 98.76x | 36.5s |
| 13_SP-UVR-4B-44100-1 | 97.78x | 36.8s |
| 14_SP-UVR-4B-44100-2 | 94.97x | 37.9s |
| 5_HP-Karaoke-UVR | 94.72x | 38.0s |
| 2_HP-UVR | 93.94x | 38.3s |
| UVR-De-Echo-Aggressive | 90.99x | 39.6s |
| UVR-DeNoise | 90.39x | 39.8s |
| UVR-De-Echo-Normal | 87.25x | 41.3s |
| UVR-DeReverb-aufr33-jarredou_4band_v4_ms_fullband | 86.70x | 41.5s |
| UVR-DeEcho-DeReverb | 86.58x | 41.6s |
| 3_HP-Vocal-UVR | 85.15x | 42.3s |
| 4_HP-Vocal-UVR | 84.23x | 42.7s |
| 1_HP-UVR | 84.06x | 42.8s |
| 17_HP-Wind_Inst-UVR | 82.92x | 43.4s |
| 6_HP-Karaoke-UVR | 81.81x | 44.0s |
| UVR-BVE-4B_SN-44100-1 | 81.54x | 44.2s |
| 9_HP2-UVR | 58.48x | 61.6s |
| 8_HP2-UVR | 57.23x | 62.9s |
| 7_HP2-UVR | 56.10x | 64.2s |

## Contributing
Contributions are welcome! 
