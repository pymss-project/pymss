"""Unified DAG execution core for pymss workflows.

This module is the single execution engine shared by:

* :mod:`pymss.graph.comfy_loader` — loads native comfy-mss JSON graphs.
* :mod:`pymss.graph.yaml_compiler` — compiles the legacy linear YAML workflow into a DAG.

Design constraints:

* Zero dependency on the ComfyUI runtime. We only parse the comfy-mss JSON
  structure and re-implement node semantics on top of pymss' own
  :class:`pymss.separator.MSSeparator`, :mod:`pymss.audio_io`, and the
  capability pool from :mod:`pymss.plugins`.
* Node executors consume built-in capabilities (invert_phase, normalize_peak,
  ensemble, {fmt}_encode, ...) rather than reimplementing DSP — pymss eats its
  own dogfood.
* ``OUTPUT_NODE`` s (e.g. ``pymss_save_audio``) are the only nodes that write
  to disk; everything else passes artifacts around in memory.

The node registry is the plugin system's (``pymss.plugins``); graph nodes
register through :func:`pymss.plugins.register_node` with an optional
``signature`` factory and the executor reads them back via
:func:`get_node_type`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..plugins.registry import _REGISTRY as _PLUGIN_REGISTRY


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


@dataclass
class AudioArtifact:
    """A single in-memory audio buffer.

    ``audio`` is stored channel-first as ``[channels, samples]`` float32.
    """

    audio: np.ndarray
    sample_rate: int
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

# Port type tags.
AUDIO = "AUDIO"
STRING = "STRING"
MSS_PARAMS = "PYMSS_MSS_PARAMS"
VR_PARAMS = "PYMSS_VR_PARAMS"


# ---------------------------------------------------------------------------
# Node signatures
# ---------------------------------------------------------------------------


@dataclass
class PortSpec:
    name: str
    type: str
    shape: int | None = None
    label: str | None = None


@dataclass
class NodeSignature:
    """Static description of a node type."""

    inputs: list[PortSpec]
    output_names: list[str] | None
    output_types: list[str] | None
    is_output_node: bool = False
    is_list: bool = False


NodeExecute = Callable[["NodeContext", dict[str, Artifact]], "NodeResult"]


@dataclass
class NodeTypeInfo:
    """A registered node type: signature factory + executor."""

    type: str
    signature: Callable[["DAGNode"], NodeSignature]
    execute: NodeExecute


# ---------------------------------------------------------------------------
# Node registry (delegates to the plugin system's registry)
# ---------------------------------------------------------------------------


def register_node(
    node_type: str,
    *,
    signature: Callable[["DAGNode"], NodeSignature],
    execute: NodeExecute,
) -> None:
    """Register a graph node type.

    Stored in the plugin system's registry so graph nodes and plugin nodes
    share one pool. The signature factory is carried in the registration's
    ``signature`` field; the executor in ``func``.
    """
    _PLUGIN_REGISTRY.register_node(
        node_type,
        execute,
        source="builtin",
        signature=signature,
    )


def register_alias(alias: str, canonical: str) -> None:
    """Register ``alias`` as another name for an already-registered ``canonical`` type.

    comfy-mss graphs in the wild use inconsistent node-type naming: comfy-mss
    upstream registers ``mss_separate``, but graphs exported from some
    front-ends carry a ``pymss_`` prefix. Aliases let both run.
    """
    target = _PLUGIN_REGISTRY.nodes.get(canonical)
    if target is None:
        raise KeyError(f"cannot alias {alias!r}: canonical type {canonical!r} is not registered")
    _PLUGIN_REGISTRY.nodes[alias] = target


class UnknownNodeError(KeyError):
    """Raised when a graph references a node type that has no executor."""

    def __init__(self, node_type: str) -> None:
        self.node_type = node_type
        super().__init__(node_type)


def get_node_type(node_type: str) -> NodeTypeInfo:
    """Look up a node type, triggering built-in registration on first call."""
    _load_builtin_nodes()
    reg = _PLUGIN_REGISTRY.nodes.get(node_type)
    if reg is None:
        raise UnknownNodeError(node_type)
    # Signature defaults to an empty signature if the registration is a plain
    # plugin node (no graph signature); graph nodes carry their own.
    sig = reg.signature
    if sig is None:
        sig = lambda node: NodeSignature(inputs=[], output_names=[], output_types=[])  # noqa: E731
    return NodeTypeInfo(type=node_type, signature=sig, execute=reg.func)


# ---------------------------------------------------------------------------
# Graph structure
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
    """A node instance inside a DAG."""

    id: object
    type: str
    inputs: list[DAGLink | None] = field(default_factory=list)
    signature: NodeSignature = field(default_factory=lambda: NodeSignature(inputs=[], output_names=[], output_types=[]))
    data: dict[str, Any] = field(default_factory=dict)
    title: str = ""
    _explicit_order: int | None = None


@dataclass
class NodeResult:
    """What a node executor returns."""

    outputs: dict[int, Artifact] = field(default_factory=dict)
    saved_paths: list[str] = field(default_factory=list)


@dataclass
class NodeContext:
    """Per-execution services handed to every node executor."""

    output_dir: Path
    logger: Any
    debug: bool
    progress_callback: Callable[[int, int, str | None], None] | None
    separator_cache: "SeparatorCache"
    input_path: str | None = None
    input_paths: list[str] = field(default_factory=list)
    strict: bool = True
    model_dir: str | os.PathLike | None = None
    download: bool = False
    source: str = "modelscopes"
    endpoint: str | None = None
    device: str | None = None
    output_format: str | None = None
    audio_params: dict[str, Any] = field(default_factory=dict)
    nodes_by_id: dict[object, "DAGNode"] = field(default_factory=dict)
    current_node_id: object | None = None
    name_prefix: str = ""

    def require(self, capability_name: str) -> Callable[..., Any]:
        """Look up a capability by name (delegates to the plugin registry)."""
        return _PLUGIN_REGISTRY.get_capability(capability_name)


# ---------------------------------------------------------------------------
# Separator cache
# ---------------------------------------------------------------------------


class SeparatorCache:
    """Reuse loaded separators within a single run.

    Keyed by a description tuple that captures everything that changes the
    loaded weights/config. Store-dir/output-format are execution-time concerns
    and are NOT part of the key.
    """

    def __init__(self, factory: Callable[..., Any] | None = None) -> None:
        self._entries: dict[str, Any] = {}
        self._factory = factory or self._default_factory

    @staticmethod
    def _default_factory(**kwargs: Any) -> Any:
        from ..separator import MSSeparator

        model_path = kwargs.pop("model_path", None)
        if model_path:
            kwargs.pop("model_dir", None)
            model_type = kwargs.pop("model_type")
            config_path = kwargs.pop("config_path", None)
            return MSSeparator(
                model_type=model_type, model_path=model_path, config_path=config_path, **kwargs
            )
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


# ---------------------------------------------------------------------------
# Value helpers (shared by executors)
# ---------------------------------------------------------------------------


def _make_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _make_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_make_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class DAGError(ValueError):
    """Raised for malformed graphs: cycles, dangling links, bad widgets."""


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


def numpy_to_audio(
    value: np.ndarray, sample_rate: int, *, stem_name: str = "", source_path: str = ""
) -> AudioArtifact:
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


def ctx_node_of(ctx: NodeContext, node_type: str) -> DAGNode:
    """Return the DAGNode currently being executed (looked up by id)."""
    return ctx.nodes_by_id[ctx.current_node_id]


# ---------------------------------------------------------------------------
# Topological ordering
# ---------------------------------------------------------------------------


def topological_order(nodes: Sequence[DAGNode]) -> list[DAGNode]:
    """Return nodes in dependency order (Kahn's algorithm)."""
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
    # it as authoritative (it encodes the topo sort the editor computed).
    if all(getattr(n, "_explicit_order", None) is not None for n in nodes):
        ordered = sorted(nodes, key=lambda n: getattr(n, "_explicit_order"))
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

    index = {node.id: i for i, node in enumerate(nodes)}
    order: list[DAGNode] = []
    ready = sorted(
        (node.id for node in nodes if not incoming[node.id]), key=lambda nid: index[nid]
    )
    pending = dict(incoming)

    while ready:
        nid = ready.pop(0)
        node = by_id[nid]
        order.append(node)
        for child_id in outgoing[nid]:
            child_links = {
                link.link_id
                for link in by_id[child_id].inputs
                if link is not None and link.source_node_id == nid
            }
            pending[child_id] -= child_links
            if not pending[child_id] and child_id not in {n.id for n in order} and child_id not in ready:
                _bisect_insert(ready, child_id, key=lambda rid: index[rid])

    if len(order) != len(nodes):
        remaining = [by_id[nid] for nid in by_id if nid not in {n.id for n in order}]
        raise DAGError(
            "workflow graph has a cycle involving: " + ", ".join(repr(n.id) for n in remaining)
        )
    return order


def _bisect_insert(
    sorted_list: list[object], value: object, *, key: Callable[[object], int]
) -> None:
    """Insert ``value`` into ``sorted_list`` keeping it sorted by ``key``."""
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
    source: str = "modelscopes",
    endpoint: str | None = None,
    device: str | None = None,
    output_format: str | None = None,
    audio_params: dict[str, Any] | None = None,
    separator_cache: SeparatorCache | None = None,
    name_prefix: str = "",
) -> list[str]:
    """Execute a DAG and return the list of files written by output nodes."""
    _load_builtin_nodes()
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
            if (
                not node.signature.inputs
                and not node.signature.output_names
                and not node.signature.output_types
            ):
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
                        logger.warning(
                            "Skipping unknown node type %r (id=%r)", exc.node_type, node.id
                        )
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
    meta: dict[str, Any] = field(default_factory=dict)

    def node(self, node_id: object) -> DAGNode:
        for node in self.graph_nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)

    # Alias retained for clarity in executor code.
    graph_nodes = property(lambda self: self.nodes)


# Filled in by ``_load_builtin_nodes``. Kept as a module-level set so loaders
# can classify nodes without poking the registry directly.
OUTPUT_NODE_TYPES: set[str] = set()


def _load_builtin_nodes() -> None:
    """Register the built-in comfy-mss node executors on first call."""
    global _builtins_loaded
    if _builtins_loaded:
        return
    from . import nodes  # noqa: F401  (side-effect: registers comfy-mss nodes)
    from . import builtin_nodes  # noqa: F401  (side-effect: registers ComfyUI built-in nodes)

    OUTPUT_NODE_TYPES.update(nodes.OUTPUT_NODE_TYPES)
    OUTPUT_NODE_TYPES.update(builtin_nodes.OUTPUT_NODE_TYPES)
    _builtins_loaded = True


_builtins_loaded = False


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
    "ctx_node_of",
    "get_node_type",
    "numpy_to_audio",
    "parse_default_int",
    "parse_device_ids",
    "register_alias",
    "register_node",
    "run_dag",
    "safe_filename_part",
    "string_value",
    "topological_order",
    "widget",
]
