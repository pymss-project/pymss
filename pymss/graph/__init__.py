"""Unified DAG execution core for pymss workflows.

This subpackage is the single engine shared by:

* native comfy-mss JSON graphs (:func:`load_comfy_file`)
* the legacy linear YAML workflow (:func:`compile_workflow_to_dag`)

Both compile down to the same :class:`DAG` and run through :func:`run_dag`,
so a folder batch (via :class:`LegacyWorkflowRunner`) and a comfy-mss graph
share separator caching, progress reporting, and audio IO.

Public API is re-exported here so callers can ``from pymss.graph import ...``
without knowing the internal module layout.
"""

from __future__ import annotations

from .core import (
    AUDIO,
    AudioArtifact,
    DAG,
    DAGError,
    DAGLink,
    DAGNode,
    MSS_PARAMS,
    NodeContext,
    NodeResult,
    NodeSignature,
    OUTPUT_NODE_TYPES,
    ParamsArtifact,
    PortSpec,
    SeparatorCache,
    STRING,
    StringArtifact,
    UnknownNodeError,
    VR_PARAMS,
    get_node_type,
    register_node,
    run_dag,
    topological_order,
)
from .comfy_loader import load_comfy_file, load_comfy_graph
from .yaml_compiler import compile_workflow_to_dag
from .runner import LegacyWorkflowRunner

__all__ = [
    "AUDIO",
    "AudioArtifact",
    "DAG",
    "DAGError",
    "DAGLink",
    "DAGNode",
    "LegacyWorkflowRunner",
    "MSS_PARAMS",
    "NodeContext",
    "NodeResult",
    "NodeSignature",
    "OUTPUT_NODE_TYPES",
    "ParamsArtifact",
    "PortSpec",
    "SeparatorCache",
    "STRING",
    "StringArtifact",
    "UnknownNodeError",
    "VR_PARAMS",
    "compile_workflow_to_dag",
    "get_node_type",
    "load_comfy_file",
    "load_comfy_graph",
    "register_node",
    "run_dag",
    "topological_order",
]
