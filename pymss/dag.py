"""Unified DAG execution core for pymss workflows.

This module is the single execution engine shared by:

* :mod:`pymss.comfy_loader` — loads native comfy-mss JSON graphs.
* :mod:`pymss.yaml_to_dag` — compiles the legacy linear YAML workflow into a DAG.

Design constraints (see goal acceptance criteria):

* Zero dependency on the ComfyUI runtime. We only parse the comfy-mss JSON
  structure and re-implement the handful of node semantics ourselves on top of
  pymss' own :class:`pymss.separator.MSSeparator`, :mod:`pymss.audio_io`, and
  :mod:`pymss.ensemble`.
* Progress is reported through pymss' own ``progress_callback(done, total,
  message)`` contract, with ``message`` carrying the active node id.
* ``OUTPUT_NODE``\\ s (e.g. ``pymss_save_audio``) are the only nodes that write
  to disk; everything else passes artifacts around in memory.

The public entry points are :class:`DAG`, :class:`DAGNode`, :func:`run_dag`,
and the in-memory artifact dataclasses.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


@dataclass
class AudioArtifact:
    """A single in-memory audio buffer.

    ``audio`` is stored channel-first as ``[channels, samples]`` float32, which
    matches what pymss separator inputs/outputs use after the comfy-mss style
    transpose. This keeps the ensemble / invert / normalize helpers branch-free.
    """

    audio: np.ndarray
    sample_rate: int
    # Optional provenance, used to name saved files when no explicit filename
    # is wired into a save node (mirrors comfy-mss ``pymss_source_path`` /
    # ``pymss_stem_name`` metadata).
    source_path: str = ""
    stem_name: str = ""

    def __post_init__(self) -> None:
        arr = np.asarray(self.audio, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr[None, :]
        if arr.ndim != 2:
            raise ValueError(f"AudioArtifact expects 1D/2D audio, got shape {arr.shape}")
        self.audio = np.ascontiguousarray(arr, dtype=np.float32)
        self.sample_rate = int(self.sample_rate)


@dataclass
class StringArtifact:
    value: str


@dataclass
class ParamsArtifact:
    """Opaque parameter dict produced by ``pymss_mss_params`` / ``pymss_vr_params``.

    Carries the ``params_type`` tag ("mss" or "vr") so separate nodes can reject
    a mismatched params source instead of silently misinterpreting it.
    """

    params: dict[str, Any]
    params_type: str  # "mss" | "vr"


Artifact = Any  # AudioArtifact | StringArtifact | ParamsArtifact | list[...]


# ---------------------------------------------------------------------------
# Node registry
# ---------------------------------------------------------------------------

AUDIO = "AUDIO"
STRING = "STRING"
MSS_PARAMS = "PYMSS_MSS_PARAMS"
VR_PARAMS = "PYMSS_VR_PARAMS"


@dataclass
class PortSpec:
    name: str
    type: str
    # ComfyUI ``shape`` is cosmetic (socket shape); we keep it only so loaders
    # can round-trip it without dropping information.
    shape: int | None = None
    label: str | None = None


@dataclass
class NodeSignature:
    """Static description of a node type.

    ``output_names`` may return ``None`` to signal that the outputs are dynamic
    (determined at load time from the node's own data, e.g. separation stems).
    """

    inputs: list[PortSpec]
    output_names: list[str] | None
    output_types: list[str] | None
    is_output_node: bool = False
    is_list: bool = False  # produces/consumes list-typed ports (``OUTPUT_IS_LIST``)


NodeExecute = Callable[["NodeContext", dict[str, Artifact]], "NodeResult"]


_REGISTRY: dict[str, NodeTypeInfo] = {}


@dataclass
class NodeTypeInfo:
    """A registered node type: signature factory + executor."""

    type: str
    signature: Callable[["DAGNode"], NodeSignature]
    execute: NodeExecute


def register_node(node_type: str, *, signature: Callable[["DAGNode"], NodeSignature], execute: NodeExecute) -> None:
    """Register a node type. Idempotent: later registrations replace earlier ones."""
    _REGISTRY[node_type] = NodeTypeInfo(type=node_type, signature=signature, execute=execute)


def get_node_type(node_type: str) -> NodeTypeInfo:
    try:
        return _REGISTRY[node_type]
    except KeyError as exc:  # pragma: no cover - exercised via run_dag(strict=)
        raise UnknownNodeError(node_type) from exc


class UnknownNodeError(KeyError):
    """Raised when a graph references a node type that has no executor."""

    def __init__(self, node_type: str) -> None:
        super().__init__(node_type)
        self.node_type = node_type


# ---------------------------------------------------------------------------
# DAG model
# ---------------------------------------------------------------------------


@dataclass
class DAGLink:
    link_id: int
    source_node_id: object
    source_slot: int
    target_node_id: object
    target_slot: int
    type: str


@dataclass
class DAGNode:
    """A node instance inside a DAG.

    ``id`` is kept as whatever the source graph used (int for comfy-mss JSON,
    str for YAML-compiled steps) so loaders do not have to rewrite ids.
    """

    id: object
    type: str
    # Ordered input slot values. ``None`` means "not connected"; the executor
    # falls back to the node's widget defaults in that case.
    inputs: list[DAGLink | None] = field(default_factory=list)
    # Resolved at signature time; cached here so topo order + output wiring can
    # read it without re-resolving.
    signature: NodeSignature = field(default_factory=lambda: NodeSignature(inputs=[], output_names=[], output_types=[]))
    # Raw node data: comfy widgets_values or YAML step fields. Executors read
    # their knobs from here.
    data: dict[str, Any] = field(default_factory=dict)
    # Title for progress / error messages.
    title: str = ""


@dataclass
class NodeResult:
    """What a node executor returns.

    ``outputs`` maps output slot index -> artifact. List-typed outputs put a
    Python ``list`` of artifacts under a single slot.
    """

    outputs: dict[int, Artifact] = field(default_factory=dict)
    # Side effects (saved file paths) for output nodes.
    saved_paths: list[str] = field(default_factory=list)


@dataclass
class NodeContext:
    """Per-execution services handed to every node executor.

    Loaders/compilers construct one of these per :func:`run_dag` call and share
    it across nodes so separators, progress, and IO helpers are consistent.
    """

    output_dir: Path
    logger: Any
    debug: bool
    progress_callback: Callable[[int, int, str | None], None] | None
    # Separator cache keyed by a stable description string. Executors ask for a
    # separator via ``get_separator``; the cache decides whether to build a new
    # one or reuse an existing instance. This is what lets a YAML folder batch
    # (and repeated comfy-mss nodes) avoid reloading weights.
    separator_cache: "SeparatorCache"
    # Input override: when the DAG is run for a specific input file (the common
    # case), loaders stash the resolved path here so ``pymss_load_audio`` /
    # ``input_audio`` nodes can read it without a hard-coded widget value.
    input_path: str | None = None
    # Input batch: when running a folder through a YAML workflow, the runner
    # expands inputs one at a time, but a comfy-mss ``pymss_load_audio_batch``
    # node drives its own multi-file expansion. We keep both modes supported.
    input_paths: list[str] = field(default_factory=list)
    # Strict mode: when False, unknown node types are skipped (with a warning)
    # instead of raising. Set by run_dag caller.
    strict: bool = True
    # User-provided model resolution knobs forwarded to MSSeparator.
    model_dir: str | os.PathLike | None = None
    download: bool = False
    source: str = "modelscope"
    endpoint: str | None = None
    # Default device/format/audio_params applied when a node does not specify
    # its own. Comfy graphs carry these per-node; YAML workflows carry them in
    # ``defaults``.
    device: str | None = None
    output_format: str | None = None
    audio_params: dict[str, Any] = field(default_factory=dict)
    # Resolved node lookup, for error messages and dynamic wiring.
    nodes_by_id: dict[object, "DAGNode"] = field(default_factory=dict)
    # The id of the node currently being executed. Set by ``run_dag`` right
    # before each executor call so node executors can look up their own
    # ``DAGNode`` (and thus their widgets) without it being passed explicitly.
    current_node_id: object | None = None
    # Optional filename prefix for saved outputs. The YAML runner sets this to
    # the track name so files land as ``<track>_<stem>.wav`` to match the legacy
    # naming; comfy-mss graphs leave it empty (filenames derive from stems).
    name_prefix: str = ""


# ---------------------------------------------------------------------------
# Separator cache
# ---------------------------------------------------------------------------


class SeparatorCache:
    """Reuse loaded separators within a single run.

    Keyed by a description tuple that captures everything that changes the
    loaded weights/config: model identity, device, inference params, tta, and
    audio params. Store-dir/output-format are execution-time concerns and are
    NOT part of the key (comfy-mss separate nodes do not save through the
    separator — only ``pymss_save_audio`` writes files).
    """

    def __init__(self, factory: Callable[..., Any] | None = None) -> None:
        self._entries: dict[str, Any] = {}
        self._factory = factory or self._default_factory

    @staticmethod
    def _default_factory(**kwargs: Any) -> Any:
        # Mirrors pymss.workflow._default_separator_factory but kept local so
        # dag.py does not import workflow.py (workflow.py imports dag.py).
        from .separator import MSSeparator

        model_path = kwargs.pop("model_path", None)
        if model_path:
            kwargs.pop("model_dir", None)
            model_type = kwargs.pop("model_type")
            config_path = kwargs.pop("config_path", None)
            return MSSeparator(model_type=model_type, model_path=model_path, config_path=config_path, **kwargs)
        model_name = kwargs.pop("model_name")
        return MSSeparator.from_model_name(model_name, **kwargs)

    @staticmethod
    def key_for(**kwargs: Any) -> str:
        blob = json.dumps(_make_jsonable(kwargs), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def get(self, **kwargs: Any) -> Any:
        key = self.key_for(**kwargs)
        entry = self._entries.get(key)
        if entry is None:
            entry = self._factory(**kwargs)
            self._entries[key] = entry
        return entry

    def close(self) -> None:
        for separator in self._entries.values():
            close = getattr(separator, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:  # pragma: no cover - best-effort cleanup
                    pass
        self._entries.clear()

    def __enter__(self) -> "SeparatorCache":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _make_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _make_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_make_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


# ---------------------------------------------------------------------------
# Topological ordering
# ---------------------------------------------------------------------------


class DAGError(ValueError):
    """Raised for malformed graphs: cycles, dangling links, bad widgets."""


def topological_order(nodes: Sequence[DAGNode]) -> list[DAGNode]:
    """Return nodes in dependency order.

    Uses the explicit link graph (edges = ``source -> target``). Nodes with no
    incoming links come first. Raises :class:`DAGError` on cycles or links that
    reference unknown nodes/slots.
    """

    by_id: dict[object, DAGNode] = {node.id: node for node in nodes}
    incoming: dict[object, set[int]] = {node.id: set() for node in nodes}
    outgoing: dict[object, list[object]] = {node.id: [] for node in nodes}

    for node in nodes:
        for link in node.inputs:
            if link is None:
                continue
            if link.source_node_id not in by_id:
                raise DAGError(
                    f"node {node.id!r} input references unknown source node {link.source_node_id!r}"
                )
            if link.target_node_id != node.id:
                raise DAGError(
                    f"node {node.id!r} carries a link whose target is {link.target_node_id!r}"
                )
            incoming[node.id].add(link.link_id)
            outgoing[link.source_node_id].append(node.id)

    # ComfyUI stores an explicit ``order`` field; if every node has one we treat
    # it as authoritative (it already encodes the topo sort the editor computed).
    if all(getattr(n, "_explicit_order", None) is not None for n in nodes):
        ordered = sorted(nodes, key=lambda n: getattr(n, "_explicit_order"))
        # Still validate no edge goes backwards.
        seen: set[object] = set()
        for n in ordered:
            for link in n.inputs:
                if link is None:
                    continue
                if link.source_node_id not in seen:
                    raise DAGError(
                        f"node {n.id!r} depends on {link.source_node_id!r} which appears later in explicit order"
                    )
            seen.add(n.id)
        return list(ordered)

    # Kahn's algorithm with a deterministic tie-breaker (original sequence).
    order: list[DAGNode] = []
    index = {node.id: i for i, node in enumerate(nodes)}
    ready = sorted(
        (node.id for node in nodes if not incoming[node.id]),
        key=lambda nid: index[nid],
    )
    pending = dict(incoming)

    while ready:
        nid = ready.pop(0)
        node = by_id[nid]
        order.append(node)
        for child_id in outgoing[nid]:
            # Drop every link from nid into child_id at once.
            child_links = {
                link.link_id
                for link in by_id[child_id].inputs
                if link is not None and link.source_node_id == nid
            }
            pending[child_id] -= child_links
            if not pending[child_id] and child_id not in {n.id for n in order} and child_id not in ready:
                ins = bisect_insert(ready, child_id, key=lambda rid: index[rid])
                continue

    if len(order) != len(nodes):
        remaining = [by_id[nid] for nid in by_id if nid not in {n.id for n in order}]
        raise DAGError(
            "workflow graph has a cycle involving: "
            + ", ".join(repr(n.id) for n in remaining)
        )
    return order


def bisect_insert(sorted_list: list[object], value: object, *, key: Callable[[object], int]) -> None:
    """Insert ``value`` into ``sorted_list`` keeping it sorted by ``key``.

    Tiny helper so topo order stays deterministic without importing bisect with
    a key wrapper (Python <3.10 ``bisect`` has no ``key`` arg).
    """

    kv = key(value)
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(sorted_list[mid]) < kv:
            lo = mid + 1
        else:
            hi = mid
    sorted_list.insert(lo, value)


# ---------------------------------------------------------------------------
# Value resolution helpers (shared by executors)
# ---------------------------------------------------------------------------


def widget(values: Sequence[Any] | None, index: int, default: Any = None) -> Any:
    """Read a widget value by index, tolerating short lists."""

    if not values:
        return default
    if 0 <= index < len(values):
        value = values[index]
        return default if value is None else value
    return default


def parse_default_int(value: Any, name: str = "value") -> int | None:
    """Parse comfy-mss ``"Default"`` / integer widget strings."""

    text = str(value if value is not None else "").strip()
    if not text or text.lower() == "default":
        return None
    try:
        parsed = int(text)
    except ValueError as exc:
        raise DAGError(f"{name} must be 'Default' or a positive integer, got {value!r}") from exc
    if parsed <= 0:
        raise DAGError(f"{name} must be a positive integer, got {parsed}")
    return parsed


def parse_device_ids(raw: Any) -> list[int]:
    values = [int(item.strip()) for item in str(raw or "0").split(",") if str(item).strip()]
    return values or [0]


def audio_to_numpy(audio: Artifact) -> tuple[np.ndarray, int]:
    """Extract a channel-first ``[channels, samples]`` float32 array."""

    if not isinstance(audio, AudioArtifact):
        raise DAGError("expected an AUDIO input")
    return np.asarray(audio.audio, dtype=np.float32), int(audio.sample_rate)


def numpy_to_audio(value: np.ndarray, sample_rate: int, *, stem_name: str = "", source_path: str = "") -> AudioArtifact:
    arr = np.asarray(value, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[None, :]
    elif arr.ndim == 2:
        # pymss separators return [samples, channels]; we store channel-first.
        if arr.shape[0] > arr.shape[1] and arr.shape[1] <= 8:
            arr = arr.T
    else:
        raise DAGError(f"unsupported audio shape {arr.shape}")
    return AudioArtifact(arr, int(sample_rate), source_path=source_path, stem_name=stem_name)


def string_value(artifact: Artifact) -> str:
    if isinstance(artifact, StringArtifact):
        return artifact.value
    if isinstance(artifact, str):
        return artifact
    if artifact is None:
        return ""
    raise DAGError(f"expected a STRING input, got {type(artifact).__name__}")


def safe_filename_part(value: str) -> str:
    text = str(value or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9_.\-]+", "_", text).strip("._")
    return cleaned or "audio"


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def run_dag(
    dag: "DAG",
    *,
    output_dir: str | os.PathLike,
    input_path: str | os.PathLike | None = None,
    input_paths: Sequence[str | os.PathLike] | None = None,
    logger: Any = None,
    debug: bool = False,
    progress_callback: Callable[[int, int, str | None], None] | None = None,
    strict: bool = True,
    model_dir: str | os.PathLike | None = None,
    download: bool = False,
    source: str = "modelscope",
    endpoint: str | None = None,
    device: str | None = None,
    output_format: str | None = None,
    audio_params: dict[str, Any] | None = None,
    separator_cache: SeparatorCache | None = None,
    name_prefix: str = "",
) -> list[str]:
    """Execute a DAG and return the list of files written by output nodes.

    ``input_path`` is the single audio file the graph should operate on; comfy
    graphs that start from ``pymss_load_audio`` pick it up through the context.
    ``input_paths`` drives ``pymss_load_audio_batch``. The two are independent —
    a graph may use either or both (though comfy-mss graphs typically use one).
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    owns_cache = separator_cache is None
    cache = separator_cache or SeparatorCache()
    try:
        ctx = NodeContext(
            output_dir=output_path,
            logger=logger,
            debug=debug,
            progress_callback=progress_callback,
            separator_cache=cache,
            input_path=str(input_path) if input_path else None,
            input_paths=[str(p) for p in input_paths] if input_paths else [],
            strict=strict,
            model_dir=model_dir,
            download=download,
            source=source,
            endpoint=endpoint,
            device=device,
            output_format=output_format,
            audio_params=dict(audio_params or {}),
            nodes_by_id={node.id: node for node in dag.nodes},
            name_prefix=name_prefix or "",
        )

        order = topological_order(dag.nodes)
        total = len(order)
        results: dict[object, NodeResult] = {}
        saved: list[str] = []

        for index, node in enumerate(order):
            # Ensure the node's signature is resolved. Loaders normally do this,
            # but graphs constructed by hand (tests, future callers) may not.
            if not node.signature.inputs and not node.signature.output_names and not node.signature.output_types:
                try:
                    node_info_for_sig = get_node_type(node.type)
                    node.signature = node_info_for_sig.signature(node)
                except UnknownNodeError:
                    pass
            try:
                node_info = get_node_type(node.type)
            except UnknownNodeError as exc:
                if not strict:
                    if logger is not None:
                        logger.warning("Skipping unknown node type %r (id=%r)", exc.node_type, node.id)
                    if progress_callback is not None:
                        progress_callback(index + 1, total, f"node={node.id} skipped unknown")
                    continue
                raise

            gathered: dict[str, Artifact] = {}
            for slot, link in enumerate(node.inputs):
                if link is None:
                    continue
                source_result = results.get(link.source_node_id)
                if source_result is None:
                    raise DAGError(
                        f"node {node.id!r} input #{slot} reads from node {link.source_node_id!r} "
                        "which produced no output (it may have been skipped)"
                    )
                artifact = source_result.outputs.get(link.source_slot)
                if artifact is None:
                    raise DAGError(
                        f"node {node.id!r} input #{slot} reads from "
                        f"node {link.source_node_id!r} output slot {link.source_slot}, "
                        "which was not produced"
                    )
                input_name = (
                    node.signature.inputs[slot].name
                    if slot < len(node.signature.inputs)
                    else f"input_{slot}"
                )
                gathered[input_name] = artifact

            if progress_callback is not None:
                progress_callback(index, total, f"node={node.id} type={node.type}")

            ctx.current_node_id = node.id
            result = node_info.execute(ctx, gathered)
            results[node.id] = result
            saved.extend(result.saved_paths)

            if progress_callback is not None:
                progress_callback(index + 1, total, f"node={node.id} type={node.type}")

        return saved
    finally:
        if owns_cache:
            cache.close()


# ---------------------------------------------------------------------------
# DAG container
# ---------------------------------------------------------------------------


@dataclass
class DAG:
    """A resolved graph ready to execute."""

    nodes: list[DAGNode] = field(default_factory=list)
    # Metadata carried from the source (comfy ``extra`` / YAML defaults) so
    # loaders and tests can inspect it. Not used by the executor.
    meta: dict[str, Any] = field(default_factory=dict)

    def node(self, node_id: object) -> DAGNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)


__all__ = [
    "AUDIO",
    "Artifact",
    "AudioArtifact",
    "DAG",
    "DAGError",
    "DAGLink",
    "DAGNode",
    "MSS_PARAMS",
    "NodeContext",
    "NodeResult",
    "NodeSignature",
    "NodeTypeInfo",
    "OUTPUT_NODE_TYPES",
    "ParamsArtifact",
    "PortSpec",
    "SeparatorCache",
    "STRING",
    "StringArtifact",
    "UnknownNodeError",
    "VR_PARAMS",
    "audio_to_numpy",
    "get_node_type",
    "numpy_to_audio",
    "parse_default_int",
    "parse_device_ids",
    "register_node",
    "run_dag",
    "safe_filename_part",
    "string_value",
    "topological_order",
    "widget",
]


# Filled in by ``_builtin_nodes`` import below. Kept as a module-level set so
# loaders can classify nodes without poking the registry directly.
OUTPUT_NODE_TYPES: set[str] = set()


def _load_builtin_nodes() -> None:
    """Register the built-in comfy-mss + ComfyUI-passthrough node executors.

    Imported lazily so ``dag.py`` stays importable on its own (test harnesses
    that only want the topo/runner can stub the registry).
    """

    from . import _dag_nodes  # noqa: F401  (side-effect: registers nodes)

    OUTPUT_NODE_TYPES.update(_dag_nodes.OUTPUT_NODE_TYPES)


_load_builtin_nodes()
