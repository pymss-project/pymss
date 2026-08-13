"""Plugin discovery and loading.

Two discovery mechanisms (both use the same registration API):
1. Folder scan (default, low-friction): each subdirectory of the plugins dir
   is a plugin; we import its ``__init__.py`` (or ``plugin.py``).
2. Entry points (optional, for proper packages): packages declare
   ``[project.entry-points."pymss.plugins"]`` and we import the target module.

A single plugin failing to load never blocks others: each import is wrapped in
try/except, failures are recorded, and surfaced via ``pymss plugins list``.

Plugin dir resolution order:
  1. PYMSS_PLUGINS_DIR env var
  2. ~/.pymss/plugins/
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_PLUGINS_DIR = Path.home() / ".pymss" / "plugins"
ENTRYPOINT_GROUP = "pymss.plugins"


def get_plugins_dir() -> Path:
    """Resolve the plugins directory from env var or default."""
    env = os.environ.get("PYMSS_PLUGINS_DIR")
    if env:
        return Path(env).expanduser()
    return DEFAULT_PLUGINS_DIR


@dataclass
class PluginLoadResult:
    """Record of a plugin load attempt (success or failure)."""

    name: str
    source: str  # "folder:<dir>" | "entrypoint" | "builtin"
    loaded: bool
    error: str = ""
    path: str = ""


@dataclass
class PluginLoadReport:
    """Aggregate load report across all plugins in a bootstrap run."""

    results: list[PluginLoadResult] = field(default_factory=list)
    bootstrapped: bool = False

    @property
    def loaded_names(self) -> list[str]:
        return [r.name for r in self.results if r.loaded]

    @property
    def failed(self) -> list[PluginLoadResult]:
        return [r for r in self.results if not r.loaded]


_LAST_REPORT: PluginLoadReport | None = None


def get_last_report() -> PluginLoadReport | None:
    """Return the most recent bootstrap report (for `pymss plugins list`)."""
    return _LAST_REPORT


def _import_plugin_module(modname: str, path: Path | None) -> bool:
    """Import a plugin module by name (entrypoint) or file path (folder scan).

    Returns True on success. Exceptions are logged by the caller.
    """
    if path is not None:
        # Folder scan: load the file as a top-level module under a synthetic
        # name so plugins don't need to be installed packages.
        spec = importlib.util.spec_from_file_location(modname, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load plugin module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    else:
        importlib.import_module(modname)
    return True


def _scan_folder(plugins_dir: Path, report: PluginLoadReport) -> None:
    """Import every subdirectory of plugins_dir that has an entry file."""
    if not plugins_dir.exists():
        return
    for child in sorted(plugins_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        # Prefer __init__.py, fall back to plugin.py.
        entry = None
        for candidate in ("__init__.py", "plugin.py"):
            p = child / candidate
            if p.exists():
                entry = p
                break
        if entry is None:
            report.results.append(
                PluginLoadResult(
                    name=child.name,
                    source=f"folder:{child}",
                    loaded=False,
                    error="no __init__.py or plugin.py found",
                    path=str(child),
                )
            )
            continue
        modname = f"_pymss_plugin_{child.name}"
        try:
            _import_plugin_module(modname, entry)
            report.results.append(
                PluginLoadResult(
                    name=child.name,
                    source=f"folder:{child}",
                    loaded=True,
                    path=str(entry),
                )
            )
            logger.debug("loaded plugin '%s' from %s", child.name, entry)
        except Exception as exc:  # noqa: BLE001
            report.results.append(
                PluginLoadResult(
                    name=child.name,
                    source=f"folder:{child}",
                    loaded=False,
                    error=f"{type(exc).__name__}: {exc}",
                    path=str(entry),
                )
            )
            logger.warning("plugin '%s' failed to load: %s", child.name, exc)


def _scan_entrypoints(report: PluginLoadReport) -> None:
    """Import every declared pymss.plugins entry point."""
    try:
        eps = entry_points()
    except Exception as exc:  # noqa: BLE001
        logger.debug("entry_points() failed: %s", exc)
        return
    # Compatible across Python 3.10+ (EntryPoints) and older (dict).
    group_eps = []
    try:
        group_eps = list(eps.select(group=ENTRYPOINT_GROUP))  # py3.10+
    except AttributeError:
        group_eps = list(eps.get(ENTRYPOINT_GROUP, []))  # type: ignore[union-attr]
    for ep in group_eps:
        try:
            ep.load()
            report.results.append(
                PluginLoadResult(name=ep.name, source="entrypoint", loaded=True)
            )
            logger.debug("loaded entrypoint plugin '%s'", ep.name)
        except Exception as exc:  # noqa: BLE001
            report.results.append(
                PluginLoadResult(
                    name=ep.name,
                    source="entrypoint",
                    loaded=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            logger.warning("entrypoint plugin '%s' failed: load: %s", ep.name, exc)


def bootstrap(force: bool = False) -> PluginLoadReport:
    """Discover and load all plugins.

    Idempotent: subsequent calls return the cached report unless ``force=True``.
    """
    global _LAST_REPORT
    if _LAST_REPORT is not None and _LAST_REPORT.bootstrapped and not force:
        return _LAST_REPORT

    report = PluginLoadReport(bootstrapped=True)
    plugins_dir = get_plugins_dir()
    _scan_folder(plugins_dir, report)
    _scan_entrypoints(report)
    _LAST_REPORT = report
    return report


def reset() -> None:
    """Clear the cached bootstrap report (mainly for tests)."""
    global _LAST_REPORT
    _LAST_REPORT = None


__all__ = [
    "DEFAULT_PLUGINS_DIR",
    "ENTRYPOINT_GROUP",
    "PluginLoadResult",
    "PluginLoadReport",
    "bootstrap",
    "get_plugins_dir",
    "get_last_report",
    "reset",
]
