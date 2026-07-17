# pymss

Python package for music source separation. <br>
[English]   [简体中文](./README_CN.md)

## Install

Install a PyTorch build that matches your accelerator first:

```sh
# NVIDIA CUDA example
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# AMD ROCm: follow https://pytorch.org/get-started/locally/ and choose the ROCm wheel for your Linux stack
```

For CLI and Python API usage, install:

```sh
pip install pymss
```

If you need API or WebUI, install this instead:

```sh
pip install "pymss[server]"
```

## Develop

Development requires Git, Python 3.10 or later, and [uv](https://docs.astral.sh/uv/). WebUI development also requires Node.js and npm.

Clone the Python package repository and install development dependencies:

```sh
git clone https://github.com/pymss-project/pymss
cd pymss
uv sync --group dev
```

If you need to develop or locally serve the WebUI, the WebUI source lives in a separate repository and must be built with Node.js:

```sh
git clone https://github.com/pymss-project/pymss-webui
cd pymss-webui
npm ci
npm run build
```

Copy the built WebUI assets into the Python package checkout:

```sh
cp -R dist/. ../pymss/server/webui_static/
```

Build source and wheel distributions from the Python package checkout:

```sh
cd ..
uv build
```

The test suite uses `pytest`. The migrated integration tests live in `test/` and are parameterized through `test/test_all.py`. They require local model weights, configs, and input audio; missing assets are skipped automatically.

```sh
uv run pytest test -q
```

## Usage

### CLI inference

Run inference by catalog model name. If the model, config, or auxiliary files are missing locally, the CLI downloads them automatically before inference.

```sh
pymss infer bs_roformer_voc_hyperacev2 \
  -i path/to/input_file_or_folder \
  -o results \
  --save-as-folder \
  --device auto \
  --format wav
```

`--device auto` uses Torch CUDA devices first, including ROCm/HIP builds on Linux. On Apple Silicon it uses the MLX backend by default. Use `--device mlx` to force MLX, or `--device mps` to force PyTorch MPS.
`--save-as-folder` writes each input audio file's stems under a subfolder named after that audio file, for example `results/song/song_vocals.wav`.

The default download source is ModelScope. You can choose another source or model directory:

```sh
pymss --model-dir /path/to/models infer bs_roformer_voc_hyperacev2 \
  --source hf-mirror \
  -i path/to/input_file_or_folder \
  -o results
```

When running from a source checkout without installation, use `python -m pymss.cli` instead of `pymss`.

### CLI workflow

Use a workflow file to chain multiple models automatically:

```sh
pymss workflow init -o vocal_chain.yaml
pymss workflow validate -c vocal_chain.yaml
pymss workflow run -c vocal_chain.yaml \
  -i path/to/input_file_or_folder \
  -o results \
  --download
```

In a workflow, `input: input` means the original audio, and `input: split.other` means the `other` stem produced by the `split` step. For folder inputs, workflow inference batches by step/model: step 1 runs for every input before step 2 is loaded. `save` controls which stems are written and which output subdirectory they use. By default, workflow batch outputs are grouped as `results/song/vocal/song_vocals.wav`; pass `--output-layout flat` to write them as `results/vocal/song_vocals.wav` instead. Duplicate input stems in the same batch are disambiguated with suffixes such as `song_3_vocals.wav`. Put shared inference options such as `batch_size` under `defaults.inference_params`, and put model-specific options such as each step's `overlap_size` under that step's `inference_params`.

### CLI ensemble

```sh
pymss ensemble path/to/model_a_vocals.wav path/to/model_b_vocals.wav \
  --algorithm avg_wave \
  --weights 1 0.8 \
  -o results/ensemble_vocals.wav
```

Available algorithms are `avg_wave`, `median_wave`, `min_wave`, `max_wave`, `avg_fft`, `median_fft`, `min_fft`, and `max_fft`. Input files must use the same sample rate and channel count. Files with different lengths are truncated to the shortest input. If `--weights` is omitted, every input uses weight `1`.

### Server and WebUI

Install the optional server dependencies to run a HTTP server with dynamic model loading, catalog browsing, model downloads, and an optional browser WebUI:

```sh
pip install "pymss[server]"
pymss serve --webui
```

See [server CLI docs](./docs/server/cli.md), [server API docs](./docs/server/api.md), and [server error docs](./docs/server/errors.md) for details.

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
separator.process_folder("path/to/input_file_or_folder")
```

`download=True` downloads missing model files before loading. Omit it for strict local-only loading.

`MSSeparator` can also be used as a context manager. Leaving the `with` block automatically calls `separator.close()`, which releases model references and clears backend caches where possible.

```python
from pymss import MSSeparator

with MSSeparator.from_model_name(
    "bs_roformer_voc_hyperacev2",
    download=True,
    device="auto",
    output_format="wav",
    store_dirs="results",
) as separator:
    separator.process_folder("path/to/input_file_or_folder")
```

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
    save_as_folder=False,
    audio_params={"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}, # Can be omitted
    logger=get_separation_logger(), # Can be omitted
    debug=False, # Can be omitted
    inference_params={
        "batch_size": 4,
        "overlap_size": 512,
        "chunk_size": 1024,
        "standardize": True,
        "normalize": False
    } # Can be omitted
)

# process all audio files in the folder
separator.process_folder('path/to/input_folder')
```

### Manual Constructor Parameters

For a detailed explanation of every `MSSeparator` argument, see the [MSSeparator parameter guide](./docs/msseparator.md).

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
- save_as_folder: When True and store_dirs points to one output folder, save each input audio file's stems in a subfolder named after the audio file.
- audio_params: Audio parameters including wav_bit_depth, flac_bit_depth, mp3_bit_rate, m4a_bit_rate, and m4a_aac_at_quality. Default is {"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}.
- logger: Logger instance. Default is pymss.get_separation_logger()
- debug: Whether to enable debug mode, default is False.
- inference_params: Inference parameters including batch_size, overlap_size, chunk_size, standardize, normalize, and `cuda_attention_backend`. `standardize` controls model input standardization and defaults to the model config's `inference.normalize` value, or `False` when missing. `normalize` controls linked output peak normalization for all returned stems. For `model_type='vr'`, supported keys are `batch_size`, `window_size`, `aggression`, `enable_tta`, `enable_post_process`, `post_process_threshold`, `high_end_process`, and output `normalize`.

### CUDA Attention Backend

RoFormer-family models default to cuDNN attention on CUDA when the installed PyTorch build exposes it. On ROCm/HIP builds they default to PyTorch's standard SDPA path. Override with `inference_params={"cuda_attention_backend": "auto"}` if you want fallback probing. Valid values are `auto`, `default`, `flash`, `cudnn`, `efficient`, `math`, and `xformers`. `auto` tries cuDNN attention first on CUDA builds, or memory-efficient SDPA first on ROCm/HIP builds, before falling back to PyTorch default SDPA. `xformers` is optional and only used if installed locally; it is not a required dependency.

### Apple Silicon MLX Backend

Use `device='mlx'` to run the Apple Silicon MLX backend:

```python
separator = MSSeparator.from_model_name(
    "bs_roformer_voc_hyperacev2",
    download=True,
    device="mlx",
    output_format="wav",
    store_dirs="results",
)
```

On Apple Silicon, `pyproject.toml` installs `mlx>=0.31.0` for this backend. If MLX is missing or a non-VR backend fails, the model records `_pymss_mlx_full_backend_error` and falls back to Torch MPS. Advanced users can still override `mps_model_backend` and `mps_model_compute_dtype` through `inference_params`.

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

### ROCm Benchmark

Measured on a Linux ROCm/HIP environment with PyTorch 2.11.0+rocm7.2 on a gfx1100 AMD GPU. Tests used a 10-minute WAV input, no TTA, one warmup run, and three measured runs. Timing covers separation only, not model loading or writing output files.

| model | type | RTFx | 1-hour audio |
|---|---|---:|---:|
| BS-Roformer-HyperACE_v2_voc | bs_roformer | 38.90x | 92.5s |
| model_bs_roformer_ep_368_sdr_12.9628 | bs_roformer | 30.27x | 118.9s |
| logic_bs_roformer | bs_roformer | 43.73x | 82.3s |
| mel-band-roformer-deux | mel_band_roformer | 38.69x | 93.0s |
| Mel-Band-Roformer-big, ep3005 candidate | mel_band_roformer | 35.83x | 100.5s |
| Mel-Band-Roformer-big, beta4 candidate | mel_band_roformer | 33.08x | 108.8s |
| HTDemucs4 | htdemucs | 14.19x | 253.7s |
| scnet_checkpoint_musdb18 | scnet | 25.45x | 141.5s |
| model_bandit_plus_dnr_sdr_11.47 | bandit | 3.31x | 1087.6s |
| checkpoint-multi_state_dict, checkpoint-eng_state_dict candidate | bandit_v2 | 7.04x | 511.4s |
| Apollo_LQ_MP3_restoration | apollo | 7.87x | 457.4s |

VR models were measured with `batch_size=2`, `window_size=512`, `aggression=5`, TTA off, post-processing off.

| VR model | RTFx | 1-hour audio |
|---|---:|---:|
| UVR-DeNoise-Lite | 60.39x | 59.6s |
| Harmonic_Noise_Separation_yxlllc | 45.63x | 78.9s |
| MGM_HIGHEND_v4 | 70.89x | 50.8s |
| MGM_LOWEND_A_v4 | 44.81x | 80.3s |
| MGM_MAIN_v4 | 39.34x | 91.5s |
| 11_SP-UVR-2B-32000-2 | 40.06x | 89.9s |
| 10_SP-UVR-2B-32000-1 | 40.21x | 89.5s |
| 12_SP-UVR-3B-44100 | 35.40x | 101.7s |

`model_vocals_mdx23c_sdr_10.17` is not present in the current catalog, so it was not measured on this branch. Some benchmark display names do not map exactly to current catalog names; those rows are marked as candidates.
