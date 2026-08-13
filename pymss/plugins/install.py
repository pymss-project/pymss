"""Plugin install / uninstall.

Three install sources:
  pymss install <name>     -> resolve <name> via official registry, git clone
  pymss install <url>      -> git clone the repo URL directly
  pymss install <path>     -> copy or symlink a local directory

Official registry: fetched from a separate pymss-plugins repo's registry.json.
The URL is configurable so the design works before that repo exists.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .loader import get_plugins_dir

logger = logging.getLogger(__name__)

# Default official registry URL. The pymss-plugins repo doesn't exist yet;
# install-by-name will report a clear error until it does. Users can override
# via PYMSS_PLUGINS_REGISTRY env var, or just install by URL/path.
DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/pymss-project/pymss-plugins/main/registry.json"
)


def _registry_url() -> str:
    return os.environ.get("PYMSS_PLUGINS_REGISTRY", DEFAULT_REGISTRY_URL)


class InstallError(Exception):
    """Raised when a plugin install fails."""


@dataclass
class InstallResult:
    name: str
    path: Path
    source: str  # "registry" | "url" | "path"


def _is_url(arg: str) -> bool:
    return arg.startswith("http://") or arg.startswith("https://") or arg.startswith("git@") or arg.startswith("ssh://")


def _git_available() -> bool:
    return shutil.which("git") is not None


def _fetch_registry() -> dict[str, str]:
    """Fetch and parse the official registry JSON. Raises InstallError on failure."""
    url = _registry_url()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pymss"})
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise InstallError(
            f"could not fetch official plugin registry from {url}: {exc}. "
            f"Install by URL or path instead, e.g. `pymss install https://github.com/xxx/pymss-opus`."
        ) from exc
    if not isinstance(data, dict):
        raise InstallError(f"registry at {url} is not a JSON object mapping name -> url")
    return data


def _derive_plugin_name(arg: str) -> str:
    """Derive a plugin folder name from a URL or local path."""
    base = arg.rstrip("/").split("/")[-1]
    if base.endswith(".git"):
        base = base[:-4]
    # Common prefix convention; keep the full name if it doesn't match.
    for prefix in ("pymss-", "pymss_"):
        if base.startswith(prefix):
            return base[len(prefix):]
    return base


def _clone(url: str, dest: Path, subpath: str | None = None) -> None:
    """Clone a repo (shallow). If subpath is given, only that subdir is kept.

    For monorepo-style plugin collections (e.g. pymss-plugins with one subdir
    per plugin), we clone to a temp dir then copy the subdir out, so the
    installed plugin directory contains just that plugin — not the whole repo.
    """
    if not _git_available():
        raise InstallError("git is required to install plugins from a URL; please install git first.")
    if dest.exists():
        raise InstallError(f"destination already exists: {dest} (uninstall it first)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if subpath:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_repo = Path(tmp) / "repo"
            try:
                subprocess.run(  # noqa: S603, S607
                    ["git", "clone", "--depth", "1", url, str(tmp_repo)],
                    check=True, capture_output=True, text=True,
                )
            except subprocess.CalledProcessError as exc:
                raise InstallError(f"git clone failed: {exc.stderr.strip() or exc}") from exc
            subdir = tmp_repo / subpath
            if not subdir.is_dir():
                raise InstallError(
                    f"plugin subpath {subpath!r} not found in {url} (checked {subdir})"
                )
            shutil.copytree(subdir, dest)
    else:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "clone", "--depth", "1", url, str(dest)],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise InstallError(f"git clone failed: {exc.stderr.strip() or exc}") from exc


def _copy_dir(src: Path, dest: Path) -> None:
    if dest.exists():
        raise InstallError(f"destination already exists: {dest} (uninstall it first)")
    shutil.copytree(src, dest)


def install(arg: str, plugins_dir: Path | None = None, subpath: str | None = None) -> InstallResult:
    """Install a plugin by name, URL, or local path.

    subpath overrides the auto-detected subdirectory. For URLs, a trailing
    ``#path/to/subdir`` also selects a subdirectory (takes precedence over the
    subpath argument). Returns InstallResult with the resolved name and path.
    """
    plugins_dir = plugins_dir or get_plugins_dir()
    plugins_dir.mkdir(parents=True, exist_ok=True)

    if _is_url(arg):
        # A trailing #path selects a subdirectory of the repo.
        if "#" in arg:
            url_part, frag = arg.rsplit("#", 1)
            subpath = frag or subpath
            arg = url_part
        name = _derive_plugin_name(arg) if not subpath else subpath.rstrip("/").split("/")[-1]
        dest = plugins_dir / name
        _clone(arg, dest, subpath=subpath or None)
        return InstallResult(name=name, path=dest, source="url")

    local = Path(arg).expanduser()
    if local.exists() and local.is_dir():
        if subpath:
            local = local / subpath
            if not local.is_dir():
                raise InstallError(
                    f"plugin subpath {subpath!r} not found under {arg} (checked {local})"
                )
        name = local.name
        dest = plugins_dir / name
        _copy_dir(local, dest)
        return InstallResult(name=name, path=dest, source="path")

    # Otherwise treat arg as an official registry name.
    registry = _fetch_registry()
    if arg not in registry:
        available = ", ".join(sorted(registry.keys())) or "(empty)"
        raise InstallError(
            f"'{arg}' is not in the official plugin registry. "
            f"Available: {available}. Or install by URL/path."
        )
    entry = registry[arg]
    # Registry entries may be either a plain URL string, or an object
    # {"url": ..., "subpath": ...} for monorepo plugin collections.
    if isinstance(entry, dict):
        url = entry.get("url", "")
        subpath = entry.get("subpath")
        if not url:
            raise InstallError(f"registry entry for '{arg}' has no 'url' field")
    else:
        url = str(entry)
        subpath = None
    dest = plugins_dir / arg
    _clone(url, dest, subpath=subpath)
    return InstallResult(name=arg, path=dest, source="registry")


def uninstall(name: str, plugins_dir: Path | None = None) -> Path:
    """Remove an installed plugin directory. Returns the removed path."""
    plugins_dir = plugins_dir or get_plugins_dir()
    dest = plugins_dir / name
    if not dest.exists():
        raise InstallError(f"no installed plugin named '{name}' in {plugins_dir}")
    if not dest.is_dir():
        raise InstallError(f"'{name}' is not a plugin directory: {dest}")
    shutil.rmtree(dest)
    return dest


__all__ = [
    "InstallError",
    "InstallResult",
    "install",
    "uninstall",
    "DEFAULT_REGISTRY_URL",
]
