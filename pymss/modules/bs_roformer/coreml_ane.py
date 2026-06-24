from __future__ import annotations

import gc
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACKAGE_ROOT = REPO_ROOT / "benchmark_results" / "ane_export_ladder_real_activation_probe"
INPUT_FLAT_SHAPE = (1, 938, 4100)


@dataclass(frozen=True)
class CoreMLStage:
    name: str
    package: Path
    input_name: str
    output_name: str | None
    output_shape: tuple[int, ...]


def _compute_unit(name: str):
    import coremltools as ct

    return {
        "cpu_only": ct.ComputeUnit.CPU_ONLY,
        "cpu_and_gpu": ct.ComputeUnit.CPU_AND_GPU,
        "cpu_and_ne": ct.ComputeUnit.CPU_AND_NE,
        "all": ct.ComputeUnit.ALL,
    }[name]


def _stages(package_root: Path) -> tuple[CoreMLStage, ...]:
    root = Path(package_root)
    return (
        CoreMLStage(
            "entry_band_0_1",
            root / "pipeline_short_fp32links_probe/first_2_segments/first_2_segments.mlpackage",
            "input_flat",
            "h1",
            (1, 938, 62, 256),
        ),
        CoreMLStage(
            "roformer_layer_pairs_2_3",
            root / "six_2layer_packages/roformer_layer_pairs_2_3/roformer_layer_pairs_2_3.mlpackage",
            "x",
            None,
            (1, 938, 62, 256),
        ),
        CoreMLStage(
            "roformer_layer_pairs_4_5",
            root / "six_2layer_packages/roformer_layer_pairs_4_5/roformer_layer_pairs_4_5.mlpackage",
            "x",
            None,
            (1, 938, 62, 256),
        ),
        CoreMLStage(
            "roformer_layer_pairs_6_7",
            root / "six_2layer_packages/roformer_layer_pairs_6_7/roformer_layer_pairs_6_7.mlpackage",
            "x",
            None,
            (1, 938, 62, 256),
        ),
        CoreMLStage(
            "roformer_layer_pairs_8_9",
            root / "six_2layer_packages/roformer_layer_pairs_8_9/roformer_layer_pairs_8_9.mlpackage",
            "x",
            None,
            (1, 938, 62, 256),
        ),
        CoreMLStage(
            "tail_10_11_final_complex",
            root / "pipeline_tail_fp32links_probe/tail_pipeline.mlpackage",
            "h10",
            "complex_mask",
            (1, 1, 2050, 938, 2),
        ),
    )


class SegmentedCoreMLANEMaskCore:
    def __init__(
            self,
            package_root: str | Path | None = None,
            compute_unit: str = "cpu_and_ne",
            storage: str = "memory",
            memmap_dir: str | Path | None = None,
            keep_memmap: bool = False,
    ):
        self.package_root = Path(package_root) if package_root else DEFAULT_PACKAGE_ROOT
        self.compute_unit = str(compute_unit or "cpu_and_ne").lower()
        self.storage = str(storage or "memory").lower()
        if self.storage not in ("memory", "memmap"):
            raise ValueError("coreml_ane_storage must be 'memory' or 'memmap'")
        self.memmap_dir = Path(memmap_dir) if memmap_dir else DEFAULT_PACKAGE_ROOT / "tmp" / "coreml_ane_memmap"
        self.keep_memmap = bool(keep_memmap)
        self.stages = _stages(self.package_root)
        self.last_timings = []
        missing = [str(stage.package) for stage in self.stages if not stage.package.exists()]
        if missing:
            raise FileNotFoundError("Missing segmented Core ML package(s): " + ", ".join(missing))

    def predict_mask(self, x_flat: np.ndarray) -> np.ndarray:
        if self.storage == "memmap":
            return self._predict_mask_memmap(x_flat)
        return self._predict_mask_memory(x_flat)

    def _predict_mask_memory(self, x_flat: np.ndarray) -> np.ndarray:
        import coremltools as ct

        if x_flat.shape[1:] != INPUT_FLAT_SHAPE[1:]:
            raise ValueError(f"segmented Core ML ANE backend expects per-chunk shape {INPUT_FLAT_SHAPE}, got {x_flat.shape}")

        self.last_timings = []
        xs = [np.ascontiguousarray(x_flat[index:index + 1], dtype=np.float32) for index in range(x_flat.shape[0])]
        for stage in self.stages:
            load_started = time.perf_counter()
            mlmodel = ct.models.MLModel(str(stage.package), compute_units=_compute_unit(self.compute_unit))
            load_sec = float(time.perf_counter() - load_started)
            next_xs = []
            predict_sec = 0.0
            for x in xs:
                predict_started = time.perf_counter()
                out = mlmodel.predict({stage.input_name: x.astype(np.float32, copy=False)})
                predict_sec += float(time.perf_counter() - predict_started)
                y = np.asarray(out[stage.output_name] if stage.output_name else next(iter(out.values()))).astype(np.float32)
                if y.shape != stage.output_shape:
                    raise ValueError(f"{stage.name} returned {y.shape}, expected {stage.output_shape}")
                next_xs.append(np.ascontiguousarray(y))
                del out
            del mlmodel
            gc.collect()
            self.last_timings.append({"name": stage.name, "load_sec": load_sec, "predict_sec": predict_sec})
            xs = next_xs
        return np.concatenate(xs, axis=0)

    def _predict_mask_memmap(self, x_flat: np.ndarray) -> np.ndarray:
        import coremltools as ct

        if x_flat.shape[1:] != INPUT_FLAT_SHAPE[1:]:
            raise ValueError(f"segmented Core ML ANE backend expects per-chunk shape {INPUT_FLAT_SHAPE}, got {x_flat.shape}")

        self.last_timings = []
        run_dir = self.memmap_dir / f"run_{os.getpid()}_{int(time.time())}"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

        current_path = run_dir / "stage_input_flat.dat"
        current_shape = tuple(x_flat.shape)
        current = np.memmap(current_path, dtype=np.float32, mode="w+", shape=current_shape)
        current[:] = np.ascontiguousarray(x_flat, dtype=np.float32)
        current.flush()

        try:
            for stage_index, stage in enumerate(self.stages):
                load_started = time.perf_counter()
                mlmodel = ct.models.MLModel(str(stage.package), compute_units=_compute_unit(self.compute_unit))
                load_sec = float(time.perf_counter() - load_started)

                next_shape = (current_shape[0], *stage.output_shape[1:])
                next_path = run_dir / f"stage_{stage_index:02d}_{stage.name}.dat"
                next_values = np.memmap(next_path, dtype=np.float32, mode="w+", shape=next_shape)
                predict_sec = 0.0
                for chunk_index in range(current_shape[0]):
                    predict_started = time.perf_counter()
                    out = mlmodel.predict({
                        stage.input_name: np.asarray(current[chunk_index:chunk_index + 1], dtype=np.float32)
                    })
                    predict_sec += float(time.perf_counter() - predict_started)
                    y = np.asarray(out[stage.output_name] if stage.output_name else next(iter(out.values()))).astype(np.float32)
                    if y.shape != stage.output_shape:
                        raise ValueError(f"{stage.name} returned {y.shape}, expected {stage.output_shape}")
                    next_values[chunk_index] = y[0]
                    del out
                next_values.flush()
                del mlmodel, current
                gc.collect()
                if current_path.exists() and not self.keep_memmap:
                    current_path.unlink()

                current = next_values
                current_path = next_path
                current_shape = next_shape
                self.last_timings.append({"name": stage.name, "load_sec": load_sec, "predict_sec": predict_sec})

            return np.asarray(current, dtype=np.float32).copy()
        finally:
            try:
                del current
            except UnboundLocalError:
                pass
            gc.collect()
            if not self.keep_memmap:
                shutil.rmtree(run_dir, ignore_errors=True)


def _runner(module) -> SegmentedCoreMLANEMaskCore:
    package_root = getattr(module, "coreml_ane_package_root", None)
    compute_unit = getattr(module, "coreml_ane_compute_unit", "cpu_and_ne")
    storage = getattr(module, "coreml_ane_storage", "memory")
    memmap_dir = getattr(module, "coreml_ane_memmap_dir", None)
    keep_memmap = bool(getattr(module, "coreml_ane_keep_memmap", False))
    key = (
        str(package_root) if package_root else "",
        str(compute_unit).lower(),
        str(storage).lower(),
        str(memmap_dir) if memmap_dir else "",
        keep_memmap,
    )
    runner = getattr(module, "_coreml_ane_runner", None)
    if runner is None or getattr(module, "_coreml_ane_runner_key", None) != key:
        runner = SegmentedCoreMLANEMaskCore(
            package_root=package_root,
            compute_unit=compute_unit,
            storage=storage,
            memmap_dir=memmap_dir,
            keep_memmap=keep_memmap,
        )
        module._coreml_ane_runner = runner
        module._coreml_ane_runner_key = key
    return runner


def coreml_ane_forward_mask_core(module, stft_repr: torch.Tensor) -> torch.Tensor:
    if module._active_source_count() != 1:
        raise NotImplementedError("segmented Core ML ANE backend currently supports single-source BSR models only")

    device = stft_repr.device
    dtype = stft_repr.dtype
    b, fs, model_t, complex_dim = stft_repr.shape
    x_flat = stft_repr.detach().float().cpu().permute(0, 2, 1, 3).reshape(b, model_t, fs * complex_dim).numpy()
    runner = _runner(module)
    mask = runner.predict_mask(x_flat)
    module._pymss_coreml_ane_last_timings = tuple(runner.last_timings)
    return torch.from_numpy(mask).to(device=device, dtype=dtype)


def coreml_ane_forward_roformer(module, raw_audio: torch.Tensor):
    from .common import istft_roformer, stft_roformer

    stft_repr, context = stft_roformer(module, raw_audio)
    mask = coreml_ane_forward_mask_core(module, stft_repr)
    stft_complex = torch.view_as_complex(stft_repr.unsqueeze(1).contiguous())
    mask_complex = torch.view_as_complex(mask.contiguous()).type(stft_complex.dtype)
    return istft_roformer(module, stft_complex * mask_complex, context, context.audio_length)
