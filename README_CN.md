# pymss
用于音乐源分离的 Python 包。
[English](./README.md)  [简体中文]
## 安装
使用 pip 安装 `pymss` 包的示例：
```sh
pip install pymss
```
## 用法

### CLI 推理

可以直接用 catalog 里的模型名推理。如果本地缺少模型、配置或辅助文件，CLI 会在推理前自动下载。

```sh
pymss infer bs_roformer_voc_hyperacev2 \
  -i path/to/input_folder \
  -o results \
  --device auto \
  --format wav
```

默认下载源是 ModelScope。也可以指定下载源或模型目录：

```sh
pymss --model-dir /path/to/models infer bs_roformer_voc_hyperacev2 \
  --source hf-mirror \
  -i path/to/input_folder \
  -o results
```

如果是在源码目录里未安装运行，可以用 `python -m pymss.cli` 代替 `pymss`。

### Python API

直接用 catalog 里的模型名即可，不需要传 `model_type`、`model_path`、`config_path`。

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

`download=True` 会在加载前下载缺失的模型文件；如果只想使用本地已有模型，可以省略它。

### 手动模型路径

自定义权重不在模型 catalog 中时，可以使用完整构造方式。

```python
from pymss import MSSeparator, get_separation_logger
# 初始化
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
        "other": None # None 或缺少此音轨将导致不输出此音轨的文件。 此示例将在 ./output/vocals 中输出人声音轨，并忽略其他（乐器）音轨。 确保键与配置文件匹配。
    },
    audio_params={"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}, # 可以省略
    logger=get_separation_logger(), # 可以省略
    debug=False, # 可以省略
    inference_params={
        "batch_size": 4,
        "overlap_size": 512,
        "chunk_size": 1024,
        "normalize": True
    } # 可以省略
)
# 处理文件夹中的所有音频文件
separator.process_folder('path/to/input_folder')
```
### 手动构造参数
- model_type: 模型类型，例如 'htdemucs'。 必须是以下之一
    ['bs_roformer',
    'mel_band_roformer',
    'htdemucs',
    'mdx23c',
    'bandit',
    'bandit_v2',
    'scnet',
    'apollo',
    'vr']
- model_path: 模型文件路径。
- config_path: 配置文件路径。
- device: 设备类型，默认为 'auto'。 必须是以下之一 ['auto', 'cuda', 'mps', 'cpu']
- device_ids: 设备 ID 列表，默认为 [0]。
- output_format: 输出音频格式，默认为 'wav'。 必须是以下之一 ['wav', 'flac', 'mp3', 'm4a']
- use_tta: 是否使用 TTA（测试时增强），默认为 False。 使用 TTA 会使处理时间增加三倍，但质量会略有提高。
- store_dirs: 存储目录，可以是单个文件夹路径或带有乐器键的字典。
- audio_params: 音频参数，包括 wav_bit_depth、flac_bit_depth、mp3_bit_rate、m4a_bit_rate 和 m4a_aac_at_quality。 默认为 {"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}。
- logger: Logger 实例。 默认为 pymss.get_separation_logger()
- debug: 是否启用调试模式，默认为 False。
- inference_params: 推理参数，包括 batch_size、overlap_size、chunk_size、normalize 和 `cuda_attention_backend`。 默认值均为 None（意味着所有参数都取决于配置文件）。`model_type='vr'` 支持 `batch_size`、`window_size`、`aggression`、`enable_tta`、`enable_post_process`、`post_process_threshold` 和 `high_end_process`。

### CUDA Attention 后端

RoFormer 系列模型在已安装 PyTorch 暴露 cuDNN attention 时默认使用 cuDNN attention，否则使用 PyTorch 默认 SDPA 路径。需要探测式回退时可通过 `inference_params={"cuda_attention_backend": "auto"}` 覆盖。可选值为 `auto`、`default`、`flash`、`cudnn`、`efficient`、`math` 和 `xformers`。`auto` 会优先尝试 cuDNN attention，然后回退到 PyTorch memory-efficient SDPA，再回退到 PyTorch 默认 SDPA。`xformers` 是本地可选安装项，不作为必需依赖。

### Apple Silicon MLX 后端

在 `device='mps'` 时，可以通过 `inference_params` 显式启用可选 MLX 完整 forward：

```python
inference_params={
    "mps_model_backend": "mlx_full",
    "mps_model_compute_dtype": "float16",
}
```

在 Apple Silicon 上，`setup.py` 会为该后端安装 `mlx>=0.31.0`。默认推理仍使用 Torch 路径；缺少 MLX 或 backend 运行失败时，非 VR 模型会记录 `_pymss_mlx_full_backend_error` 并回退 Torch。

### 模型兼容性

配置为 `model: htdemucs` 且 `htdemucs.cac: true` 的 HTDemucs checkpoint 通过 `model_type='htdemucs'` 支持。

旧 Demucs/TasNet `.th` 权重可以使用 `model_type='legacy_demucs'` 或 `model_type='legacy_tasnet'`，不需要 MSST YAML 配置。当前无外部依赖 legacy loader 支持 classic Demucs、v3 time-domain Demucs、ConvTasNet、CaC HDemucs、package 形式 HTDemucs、multi-frequency CaC HDemucs 和简单 Demucs bag YAML。DiffQ 量化 checkpoint 和 non-CaC/Wiener HDemucs 仍需要专门的旧模型加载器。

UVR VR 支持已适配的 UVR/VR 系列 `.pth` 权重。和其他模型一样，直接用 catalog 里的模型名走 CLI 或 Python API。输出 stem 名称来自内置 VR 模型列表，例如 `Vocals`、`Instrumental`、`No Echo` 或 `Echo`。

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

### Hugging Face 配置提醒
一些从 Hugging Face 或 MSST-WebUI 下载的模型配置使用 `inference.num_overlap`。当前优化后的 pymss 路径使用 `inference.overlap_size`。如果配置里只有 `num_overlap`，请手动添加 `overlap_size`，或通过 `inference_params` 传入；否则 pymss 会回退到 50% overlap，推理会慢很多。

推荐快速设置：

```yaml
audio:
  chunk_size: 480000
inference:
  batch_size: 2
  overlap_size: 24000  # chunk_size 的 5%
```

### RTX 5090 实测

测试环境为 NVIDIA GeForce RTX 5090、PyTorch 2.9.1+cu128、CUDA 12.8，关闭 TTA，预热 1 次，正式运行 3 次。

| 模型 | 类型 | RTFx | 1 小时音频 |
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

VR 模型测试参数为 `batch_size=2`、`window_size=512`、`aggression=5`，关闭 TTA 和后处理。

| VR 模型 | RTFx | 1 小时音频 |
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

## 贡献
欢迎贡献！
