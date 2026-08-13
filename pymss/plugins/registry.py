"""Plugin system: capability registry and node/CLI registration API.

Design reference: docs/plugins.md (when ported to this branch).

Two decoupled concepts:
- Capability: a named function registered into a global pool. Does not know
  who calls it.
- Consumer: a workflow node or CLI command that looks up a capability by name.

Providers and consumers can ship in different packages, coupled only by the
capability name.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class CapabilityNotFound(KeyError):
    """Raised when a required capability is not registered.

    Consumers (nodes / CLI commands) catch this to give a more specific hint,
    e.g. "SaveAudioOpus needs the opus_encode capability; run `pymss install
    opus`".
    """

    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"capability '{name}' is not registered. Install a plugin that "
            f"provides it (e.g. `pymss install <name>`), or register it via "
            f"pymss.plugins.register_capability."
        )


@dataclass
class Capability:
    """A registered capability: a name + a callable + optional metadata."""

    name: str
    func: Callable[..., Any]
    source: str = "builtin"  # which plugin/package provided it
    description: str = ""


@dataclass
class NodeRegistration:
    """A registered workflow node executor."""

    node_type: str
    func: Callable[..., Any]
    source: str = "builtin"
    description: str = ""


@dataclass
class CLIRegistration:
    """A registered CLI subcommand path, e.g. ("opus", "encode")."""

    path: tuple[str, ...]
    func: Callable[..., Any]
    help: str = ""
    source: str = "builtin"
    add_arguments: Callable[[Any], None] | None = None  # optional argparse hook


@dataclass
class PluginRegistry:
    """Global registry for capabilities, nodes, and CLI commands.

    A single shared instance is exposed as `_REGISTRY`. pymss core registers
    built-in capabilities at startup; plugins add more via the public API.
    """

    capabilities: dict[str, Capability] = field(default_factory=dict)
    nodes: dict[str, NodeRegistration] = field(default_factory=dict)
    cli_commands: list[CLIRegistration] = field(default_factory=list)

    # Names that plugins must never override (pymss / comfy-mss built-ins).
    # Only enforced for node registrations; capabilities use last-writer-wins
    # with a warning.
    _reserved_node_types: set[str] = field(default_factory=set)

    # ---- capability API ----
    def register_capability(
        self,
        name: str,
        func: Callable[..., Any],
        *,
        source: str = "builtin",
        description: str = "",
    ) -> None:
        if name in self.capabilities and self.capabilities[name].source != source:
            logger.warning(
                "capability '%s' already registered by '%s'; overriding with '%s'",
                name,
                self.capabilities[name].source,
                source,
            )
        self.capabilities[name] = Capability(
            name=name, func=func, source=source, description=description
        )

    def get_capability(self, name: str) -> Callable[..., Any]:
        try:
            return self.capabilities[name].func
        except KeyError as exc:
            raise CapabilityNotFound(name) from exc

    def has_capability(self, name: str) -> bool:
        return name in self.capabilities

    # ---- node API ----
    def reserve_node_type(self, node_type: str) -> None:
        """Mark a node type as a pymss/comfy-mss built-in that plugins cannot override."""
        self._reserved_node_types.add(node_type)

    def register_node(
        self,
        node_type: str,
        func: Callable[..., Any],
        *,
        source: str = "builtin",
        description: str = "",
        allow_override_builtin: bool = False,
    ) -> None:
        if node_type in self._reserved_node_types and not allow_override_builtin:
            raise ValueError(
                f"node type '{node_type}' is a reserved pymss built-in and "
                f"cannot be registered by plugins."
            )
        if node_type in self.nodes:
            logger.warning(
                "node type '%s' already registered by '%s'; overriding with '%s'",
                node_type,
                self.nodes[node_type].source,
                source,
            )
        self.nodes[node_type] = NodeRegistration(
            node_type=node_type, func=func, source=source, description=description
        )

    def get_node(self, node_type: str) -> Callable[..., Any] | None:
        reg = self.nodes.get(node_type)
        return reg.func if reg else None

    # ---- CLI API ----
    def register_cli(
        self,
        path: str | tuple[str, ...],
        func: Callable[..., Any],
        *,
        help: str = "",
        source: str = "builtin",
        add_arguments: Callable[[Any], None] | None = None,
    ) -> None:
        if isinstance(path, str):
            path_tuple = tuple(path.split())
        else:
            path_tuple = tuple(path)
        if not path_tuple:
            raise ValueError("CLI command path must be non-empty")
        self.cli_commands.append(
            CLIRegistration(
                path=path_tuple,
                func=func,
                help=help,
                source=source,
                add_arguments=add_arguments,
            )
        )


# Single shared registry instance.
_REGISTRY: PluginRegistry = PluginRegistry()


# ---------------------------------------------------------------------------
# Public registration API (used by plugins via `from pymss.plugins import ...`)
# ---------------------------------------------------------------------------


def register_capability(
    name: str,
    func: Callable[..., Any] | None = None,
    *,
    source: str = "plugin",
    description: str = "",
):
    """Register a named capability, or use as a decorator.

    Usage (direct):
        register_capability("opus_encode", opus_encode_fn, source="my-plugin")

    Usage (decorator):
        @register_capability("eq")
        def eq(audio, sample_rate, low_gain=0, mid_gain=0, high_gain=0):
            ...
    """
    if func is None:
        def decorator(f: Callable[..., Any]):
            _REGISTRY.register_capability(name, f, source=source, description=description)
            return f
        return decorator
    _REGISTRY.register_capability(name, func, source=source, description=description)
    return func


def register_node(
    node_type: str,
    func: Callable[..., Any] | None = None,
    *,
    source: str = "plugin",
    description: str = "",
):
    """Register a workflow node executor. See register_capability for decorator use."""
    if func is None:
        def decorator(f: Callable[..., Any]):
            _REGISTRY.register_node(node_type, f, source=source, description=description)
            return f
        return decorator
    _REGISTRY.register_node(node_type, func, source=source, description=description)
    return func


def register_cli(
    path: str | tuple[str, ...],
    func: Callable[..., Any] | None = None,
    *,
    help: str = "",
    source: str = "plugin",
    add_arguments: Callable[[Any], None] | None = None,
):
    """Register a CLI subcommand under `pymss <path[0]> <path[1]> ...`.

    path: e.g. "opus encode" or ("opus", "encode"). The first element is the
    plugin's namespace; it must not collide with official pymss commands.
    """
    if func is None:
        def decorator(f: Callable[..., Any]):
            _REGISTRY.register_cli(
                path, f, help=help, source=source, add_arguments=add_arguments
            )
            return f
        return decorator
    _REGISTRY.register_cli(path, func, help=help, source=source, add_arguments=add_arguments)
    return func


def require_capability(name: str) -> Callable[..., Any]:
    """Look up a capability by name; raise CapabilityNotFound if missing.

    Intended for use inside node executors and CLI command handlers."""
    return _REGISTRY.get_capability(name)


def get_registry() -> PluginRegistry:
    """Return the shared plugin registry (for introspection / pymss internals)."""
    return _REGISTRY


__all__ = [
    "CapabilityNotFound",
    "PluginRegistry",
    "register_capability",
    "register_node",
    "register_cli",
    "require_capability",
    "get_registry",
    "_REGISTRY",
]
