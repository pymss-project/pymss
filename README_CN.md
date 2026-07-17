# pymss
用于音乐源分离的 Python 包。
[English](./README.md)  [简体中文]

## 安装

先安装与加速器匹配的 PyTorch 构建：

```sh
# NVIDIA CUDA 示例
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# AMD ROCm：按 https://pytorch.org/get-started/locally/ 页面选择与你的 Linux 环境匹配的 ROCm wheel
```

如果只需要 CLI 和 Python API，安装：

```sh
pip install pymss
```

如果需要使用 API 或者 WebUI，则改为安装：

```sh
pip install "pymss[server]"
```

## 开发

开发需要 Git、Python 3.10 或更高版本，以及 [uv](https://docs.astral.sh/uv/)。WebUI 开发还需要 Node.js 和 npm。

克隆 Python 包仓库，并安装开发依赖：

```sh
git clone https://github.com/pymss-project/pymss
cd pymss
uv sync --group dev
```

如果需要开发或本地运行 WebUI, WebUI 源码位于单独仓库，需要使用 Node.js 构建：

```sh
git clone https://github.com/pymss-project/pymss-webui
cd pymss-webui
npm ci
npm run build
```

把构建后的 WebUI 静态资源复制到 Python 包目录：

```sh
cp -R dist/. ../pymss/server/webui_static/
```

回到 Python 包目录，构建源码包和 wheel：

```sh
cd ..
uv build
```

测试使用 `pytest`。迁移后的集成测试位于 `test/`，统一通过 `test/test_all.py` 参数化运行。这些测试依赖本地模型权重、配置文件和输入音频；缺少资源时会自动跳过。

```sh
uv run pytest test -q
```

## 用法

### CLI 推理

可以直接用 catalog 里的模型名推理。如果本地缺少模型、配置或辅助文件，CLI 会在推理前自动下载。

```sh
pymss infer bs_roformer_voc_hyperacev2 \
  -i path/to/input_file_or_folder \
  -o results \
  --save-as-folder \
  --device auto \
  --format wav
```

`--device auto` 会优先使用 Torch 的 CUDA 设备，包括 Linux 上的 ROCm/HIP 构建；Apple Silicon Mac 默认使用 MLX 后端。可以用 `--device mlx` 强制 MLX，或用 `--device mps` 强制 PyTorch MPS。
`--save-as-folder` 会把每个输入音频的输出音轨保存到以该音频命名的子文件夹中，例如 `results/song/song_vocals.wav`。

默认下载源是 ModelScope。也可以指定下载源或模型目录：

```sh
pymss --model-dir /path/to/models infer bs_roformer_voc_hyperacev2 \
  --source hf-mirror \
  -i path/to/input_file_or_folder \
  -o results
```

如果是在源码目录里未安装运行，可以用 `python -m pymss.cli` 代替 `pymss`。

### CLI Workflow

可以用 workflow 文件把多个模型串成自动流程：

```sh
pymss workflow init -o vocal_chain.yaml
pymss workflow validate -c vocal_chain.yaml
pymss workflow run -c vocal_chain.yaml \
  -i path/to/input_file_or_folder \
  -o results \
  --download
```

workflow 中的 `input: input` 表示原始音频，`input: split.other` 表示使用 `split` 步骤输出的 `other` 音轨。文件夹输入会按 step/model 批处理：第 1 个 step 会先跑完所有输入，再加载第 2 个 step。`save` 控制保存哪些音轨以及保存到输出目录下的哪个子目录。默认批量输出会按 `results/song/vocal/song_vocals.wav` 分到每个音频的子目录；加 `--output-layout flat` 后会输出为 `results/vocal/song_vocals.wav`。同一批里输入 stem 重名时会自动加后缀，例如 `song_3_vocals.wav`。共享推理参数如 `batch_size` 可以放在 `defaults.inference_params`，每个模型单独的参数如各自的 `overlap_size` 可以放在该 step 的 `inference_params`。

### CLI Ensemble

```sh
pymss ensemble path/to/model_a_vocals.wav path/to/model_b_vocals.wav \
  --algorithm avg_wave \
  --weights 1 0.8 \
  -o results/ensemble_vocals.wav
```

可用算法包括 `avg_wave`、`median_wave`、`min_wave`、`max_wave`、`avg_fft`、`median_fft`、`min_fft` 和 `max_fft`。输入文件需要使用相同采样率和声道数；如果长度不同，会裁剪到最短输入长度。不传 `--weights` 时，每个输入默认权重都是 `1`。

### Server 和 WebUI

安装可选 server 依赖后，可以启动 HTTP server，支持动态加载模型、浏览 catalog、下载模型文件，以及可选的浏览器 WebUI：

```sh
pip install "pymss[server]"
pymss serve --webui
```

详细用法见 [server CLI 文档](./docs/server/cli.md)、[server API 文档](./docs/server/api.md) 和 [server 错误文档](./docs/server/errors.md)。

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
separator.process_folder("path/to/input_file_or_folder")
```

`download=True` 会在加载前下载缺失的模型文件；如果只想使用本地已有模型，可以省略它。

`MSSeparator` 也可以作为上下文管理器使用。退出 `with` 代码块时会自动调用 `separator.close()`，尽量释放模型引用并清理后端缓存。

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
    save_as_folder=False,
    audio_params={"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}, # 可以省略
    logger=get_separation_logger(), # 可以省略
    debug=False, # 可以省略
    inference_params={
        "batch_size": 4,
        "overlap_size": 512,
        "chunk_size": 1024,
        "standardize": True,
        "normalize": False
    } # 可以省略
)
# 处理文件夹中的所有音频文件
separator.process_folder('path/to/input_folder')
```
### 手动构造参数

每个 `MSSeparator` 参数的详细说明见 [MSSeparator 参数文档](./docs/msseparator_cn.md)。

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
- save_as_folder: 为 True 且 store_dirs 指向同一个输出文件夹时，会把每个输入音频的输出音轨保存到以音频名命名的子文件夹中。
- audio_params: 音频参数，包括 wav_bit_depth、flac_bit_depth、mp3_bit_rate、m4a_bit_rate 和 m4a_aac_at_quality。 默认为 {"wav_bit_depth": "FLOAT", "flac_bit_depth": "PCM_24", "mp3_bit_rate": "320k", "m4a_bit_rate": "192k", "m4a_aac_at_quality": 2}。
- logger: Logger 实例。 默认为 pymss.get_separation_logger()
- debug: 是否启用调试模式，默认为 False。
- inference_params: 推理参数，包括 batch_size、overlap_size、chunk_size、standardize、normalize 和 `cuda_attention_backend`。`standardize` 控制模型输入标准化，默认使用模型配置里的 `inference.normalize`，如果配置文件没有该项则为 `False`。`normalize` 控制所有输出音轨联动的峰值归一化。`model_type='vr'` 支持 `batch_size`、`window_size`、`aggression`、`enable_tta`、`enable_post_process`、`post_process_threshold`、`high_end_process` 和输出 `normalize`。

### CUDA Attention 后端

RoFormer 系列模型在已安装 PyTorch 暴露 cuDNN attention 的 CUDA 构建上默认使用 cuDNN attention；在 ROCm/HIP 构建上默认使用 PyTorch 标准 SDPA 路径。需要探测式回退时可通过 `inference_params={"cuda_attention_backend": "auto"}` 覆盖。可选值为 `auto`、`default`、`flash`、`cudnn`、`efficient`、`math` 和 `xformers`。`auto` 在 CUDA 构建上优先尝试 cuDNN attention，在 ROCm/HIP 构建上优先尝试 memory-efficient SDPA，随后都回退到 PyTorch 默认 SDPA。`xformers` 是本地可选安装项，不作为必需依赖。

### Apple Silicon MLX 后端

使用 `device='mlx'` 可以启用 Apple Silicon MLX 后端：

```python
separator = MSSeparator.from_model_name(
    "bs_roformer_voc_hyperacev2",
    download=True,
    device="mlx",
    output_format="wav",
    store_dirs="results",
)
```

在 Apple Silicon 上，`pyproject.toml` 会为该后端安装 `mlx>=0.31.0`。缺少 MLX 或 backend 运行失败时，非 VR 模型会记录 `_pymss_mlx_full_backend_error` 并回退到 Torch MPS。高级用户仍然可以通过 `inference_params` 覆盖 `mps_model_backend` 和 `mps_model_compute_dtype`。

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

### ROCm 实测

测试环境为 Linux ROCm/HIP、PyTorch 2.11.0+rocm7.2、gfx1100 AMD GPU。使用 10 分钟 WAV 输入，关闭 TTA，预热 1 次，正式运行 3 次。计时只包含分离过程，不包含模型加载和写出文件。

| 模型 | 类型 | RTFx | 1 小时音频 |
|---|---|---:|---:|
| BS-Roformer-HyperACE_v2_voc | bs_roformer | 38.90x | 92.5s |
| model_bs_roformer_ep_368_sdr_12.9628 | bs_roformer | 30.27x | 118.9s |
| logic_bs_roformer | bs_roformer | 43.73x | 82.3s |
| mel-band-roformer-deux | mel_band_roformer | 38.69x | 93.0s |
| Mel-Band-Roformer-big，ep3005 候选 | mel_band_roformer | 35.83x | 100.5s |
| Mel-Band-Roformer-big，beta4 候选 | mel_band_roformer | 33.08x | 108.8s |
| HTDemucs4 | htdemucs | 14.19x | 253.7s |
| scnet_checkpoint_musdb18 | scnet | 25.45x | 141.5s |
| model_bandit_plus_dnr_sdr_11.47 | bandit | 3.31x | 1087.6s |
| checkpoint-multi_state_dict，checkpoint-eng_state_dict 候选 | bandit_v2 | 7.04x | 511.4s |
| Apollo_LQ_MP3_restoration | apollo | 7.87x | 457.4s |

VR 模型测试参数为 `batch_size=2`、`window_size=512`、`aggression=5`，关闭 TTA 和后处理。

| VR 模型 | RTFx | 1 小时音频 |
|---|---:|---:|
| UVR-DeNoise-Lite | 60.39x | 59.6s |
| Harmonic_Noise_Separation_yxlllc | 45.63x | 78.9s |
| MGM_HIGHEND_v4 | 70.89x | 50.8s |
| MGM_LOWEND_A_v4 | 44.81x | 80.3s |
| MGM_MAIN_v4 | 39.34x | 91.5s |
| 11_SP-UVR-2B-32000-2 | 40.06x | 89.9s |
| 10_SP-UVR-2B-32000-1 | 40.21x | 89.5s |
| 12_SP-UVR-3B-44100 | 35.40x | 101.7s |

`model_vocals_mdx23c_sdr_10.17` 不在当前 catalog 中，因此本分支未测试该项。部分 benchmark 展示名无法与当前 catalog 名字完全对应，表中已标为候选。
