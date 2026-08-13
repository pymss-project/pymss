"""Plugin install / uninstall.

Three install sources:
  pymss install <name>     -> resolve <name> via official registry, git clone
  pymss install <url>      -> git clone the repo URL directly
  pymss install <path>     -> copy or symlink a local directory

Version pinning: `pymss install <name>@<ref>` checks out a git ref (tag/branch/commit).
Dependencies: read from the plugin's pyproject.toml [project].dependencies and
installed via uv (preferred for uv-managed venvs) or pip.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    version: str | None = None
    dependencies_installed: list[str] = field(default_factory=list)


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


def _clone(url: str, dest: Path, subpath: str | None = None, ref: str | None = None) -> None:
    """Clone a repo (shallow). If subpath is given, only that subdir is kept.
    If ref is given, check out that tag/branch/commit after cloning.

    For monorepo-style plugin collections (e.g. pymss-plugins with one subdir
    per plugin), we clone to a temp dir then copy the subdir out, so the
    installed plugin directory contains just that plugin — not the whole repo.
    """
    if not _git_available():
        raise InstallError("git is required to install plugins from a URL; please install git first.")
    if dest.exists():
        raise InstallError(f"destination already exists: {dest} (uninstall it first)")
    dest.parent.mkdir(parents=True, exist_ok=True)

    clone_cmd = ["git", "clone", "--depth", "1"]
    if ref:
        clone_cmd += ["--branch", ref]
    clone_cmd += [url]

    if subpath:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_repo = Path(tmp) / "repo"
            try:
                subprocess.run(  # noqa: S603, S607
                    clone_cmd + [str(tmp_repo)],
                    check=True, capture_output=True, text=True,
                )
            except subprocess.CalledProcessError as exc:
                hint = "" if not ref else f" (check that ref {ref!r} exists on the remote)"
                raise InstallError(f"git clone failed:{hint} {exc.stderr.strip() or exc}") from exc
            subdir = tmp_repo / subpath
            if not subdir.is_dir():
                raise InstallError(
                    f"plugin subpath {subpath!r} not found in {url} (checked {subdir})"
                )
            shutil.copytree(subdir, dest, ignore=shutil.ignore_patterns(".git"))
    else:
        try:
            subprocess.run(  # noqa: S603, S607
                clone_cmd + [str(dest)],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as exc:
            hint = "" if not ref else f" (check that ref {ref!r} exists on the remote)"
            raise InstallError(f"git clone failed:{hint} {exc.stderr.strip() or exc}") from exc


# ---------------------------------------------------------------------------
# Plugin metadata (read from pyproject.toml) and dependency installation
# ---------------------------------------------------------------------------

_PYPROJECT_NAME_RE = re.compile(r'^name\s*=\s*["\']([^"\']+)', re.M)
_PYPROJECT_VERSION_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)', re.M)
_PYPROJECT_DEPS_RE = re.compile(r'dependencies\s*=\s*\[(.*?)\]', re.S | re.M)


def _read_plugin_meta(plugin_dir: Path) -> dict:
    """Read name/version/dependencies from a plugin's pyproject.toml.

    Uses a regex-based parse (no tomllib needed for this simple shape, and
    stays compatible with Python 3.10 which has tomllib only in 3.11+).
    Returns {} if no pyproject.toml is present.
    """
    pp = plugin_dir / "pyproject.toml"
    if not pp.exists():
        return {}
    txt = pp.read_text(encoding="utf-8")
    meta = {}
    if m := _PYPROJECT_NAME_RE.search(txt):
        meta["name"] = m.group(1)
    if m := _PYPROJECT_VERSION_RE.search(txt):
        meta["version"] = m.group(1)
    if m := _PYPROJECT_DEPS_RE.search(txt):
        deps_raw = m.group(1)
        deps = re.findall(r'["\']([^"\']+)["\']', deps_raw)
        meta["dependencies"] = [d for d in deps if d.lower() != "pymss"]
    return meta


def _detect_package_manager() -> str | None:
    """Detect how to install packages into the current environment.

    Returns "uv" if this is a uv-managed venv (or uv is on PATH), "pip" if the
    pip module is importable, or None if neither is available.
    """
    # Check pyvenv.cfg for a uv-managed venv first — uv venvs intentionally
    # ship without pip, so we must use uv there.
    try:
        import sysconfig
        cfg = Path(sysconfig.get_config_var("prefix") or "") / "pyvenv.cfg"
        if cfg.exists() and "uv =" in cfg.read_text(encoding="utf-8"):
            if shutil.which("uv"):
                return "uv"
    except Exception:
        pass
    # Fall back to uv if it's on PATH (covers uv-managed setups without cfg).
    if shutil.which("uv"):
        return "uv"
    # Finally, pip module.
    try:
        import importlib.util
        if importlib.util.find_spec("pip") is not None:
            return "pip"
    except Exception:
        pass
    return None


def _install_dependencies(deps: list[str]) -> None:
    """Install Python dependencies into the current environment.

    Prefers uv (for uv-managed venvs), falls back to pip. Raises InstallError
    if neither is available or the install fails.
    """
    if not deps:
        return
    pm = _detect_package_manager()
    if pm is None:
        raise InstallError(
            "cannot install plugin dependencies: neither uv nor pip is available. "
            "Install them manually, e.g. `uv pip install " + " ".join(deps) + "`, "
            "or reinstall with --no-deps."
        )
    if pm == "uv":
        cmd = ["uv", "pip", "install", "--python", sys.executable, *deps]
    else:
        cmd = [sys.executable, "-m", "pip", "install", *deps]
    try:
        subprocess.run(  # noqa: S603
            cmd, check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise InstallError(
            f"dependency install failed: {exc.stderr.strip() or exc}. "
            f"You can skip this with `pymss install ... --no-deps` and install manually: "
            f"`{' '.join(deps)}`"
        ) from exc


def _write_install_manifest(
    plugin_dir: Path, *, name: str, source: str, url: str | None,
    subpath: str | None, ref: str | None, meta: dict,
) -> None:
    """Write .pymss-install.json so update/list can identify the install."""
    manifest = {
        "name": name,
        "version": meta.get("version"),
        "source": source,
        "url": url,
        "subpath": subpath,
        "ref": ref,
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (plugin_dir / ".pymss-install.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def read_install_manifest(plugin_dir: Path) -> dict:
    """Read the .pymss-install.json written at install time. Returns {} if none."""
    mf = plugin_dir / ".pymss-install.json"
    if not mf.exists():
        return {}
    try:
        return json.loads(mf.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _copy_dir(src: Path, dest: Path) -> None:
    if dest.exists():
        raise InstallError(f"destination already exists: {dest} (uninstall it first)")
    shutil.copytree(src, dest)


def install(
    arg: str,
    plugins_dir: Path | None = None,
    subpath: str | None = None,
    ref: str | None = None,
    no_deps: bool = False,
) -> InstallResult:
    """Install a plugin by name, URL, or local path.

    subpath overrides the auto-detected subdirectory. For URLs, a trailing
    ``#path/to/subdir`` also selects a subdirectory (takes precedence over the
    subpath argument). ref checks out a git tag/branch/commit (e.g. from
    ``name@0.2.0``). Dependencies from pyproject.toml are installed unless
    no_deps is True. Returns InstallResult with the resolved name and path.
    """
    plugins_dir = plugins_dir or get_plugins_dir()
    plugins_dir.mkdir(parents=True, exist_ok=True)

    # `name@ref` syntax: split off a git ref for registry/url installs.
    if ref is None and "@" in arg and not arg.startswith(("/", ".", "~")):
        arg, ref = arg.rsplit("@", 1)

    installed_deps: list[str] = []

    if _is_url(arg):
        # A trailing #path selects a subdirectory of the repo.
        if "#" in arg:
            url_part, frag = arg.rsplit("#", 1)
            subpath = frag or subpath
            arg = url_part
        name = subpath.rstrip("/").split("/")[-1] if subpath else _derive_plugin_name(arg)
        dest = plugins_dir / name
        _clone(arg, dest, subpath=subpath or None, ref=ref)
        meta = _read_plugin_meta(dest)
        if not no_deps:
            _install_dependencies(meta.get("dependencies", []))
            installed_deps = meta.get("dependencies", [])
        _write_install_manifest(dest, name=name, source="url", url=arg,
                                subpath=subpath, ref=ref, meta=meta)
        return InstallResult(name=name, path=dest, source="url",
                             version=meta.get("version"), dependencies_installed=installed_deps)

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
        meta = _read_plugin_meta(dest)
        if not no_deps:
            _install_dependencies(meta.get("dependencies", []))
            installed_deps = meta.get("dependencies", [])
        _write_install_manifest(dest, name=name, source="path",
                                url=str(Path(arg).resolve()),
                                subpath=subpath, ref=ref, meta=meta)
        return InstallResult(name=name, path=dest, source="path",
                             version=meta.get("version"), dependencies_installed=installed_deps)

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
        subpath = entry.get("subpath") or subpath
        if not url:
            raise InstallError(f"registry entry for '{arg}' has no 'url' field")
    else:
        url = str(entry)
    dest = plugins_dir / arg
    _clone(url, dest, subpath=subpath, ref=ref)
    meta = _read_plugin_meta(dest)
    if not no_deps:
        _install_dependencies(meta.get("dependencies", []))
        installed_deps = meta.get("dependencies", [])
    _write_install_manifest(dest, name=arg, source="registry", url=url,
                            subpath=subpath, ref=ref, meta=meta)
    return InstallResult(name=arg, path=dest, source="registry",
                         version=meta.get("version"), dependencies_installed=installed_deps)


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


# ---------------------------------------------------------------------------
# Browse / search the official registry
# ---------------------------------------------------------------------------

def _registry_entries() -> list[dict]:
    """Return registry entries as normalized dicts (drop _comment etc.)."""
    raw = _fetch_registry()
    out = []
    for name, entry in raw.items():
        if name.startswith("_"):
            continue
        if isinstance(entry, dict):
            e = {"name": name, **entry}
        else:
            e = {"name": name, "url": str(entry)}
        out.append(e)
    return out


def list_available() -> list[dict]:
    """List all plugins in the official registry with their metadata.

    Each entry: {name, url, subpath?, description?, tags?, installed?}.
    `installed` is True if a plugin of that name exists locally.
    """
    plugins_dir = get_plugins_dir()
    entries = _registry_entries()
    for e in entries:
        e["installed"] = (plugins_dir / e["name"]).exists()
    return entries


def search_available(query: str) -> list[dict]:
    """Search the registry by name/description/tags (case-insensitive substring)."""
    q = query.lower()
    results = []
    for e in list_available():
        haystack = " ".join([
            e.get("name", ""),
            e.get("description", ""),
            " ".join(e.get("tags", []) or []),
        ]).lower()
        if q in haystack:
            results.append(e)
    return results


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------

REMOTE_META_TIMEOUT = 15


def _fetch_remote_meta(url: str, subpath: str | None, ref: str | None) -> dict:
    """Clone a repo (shallow, optional ref) to a temp dir and read the subdir's pyproject.toml.

    Used to learn the latest version of a plugin without installing it.
    """
    import tempfile

    if not _git_available():
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp) / "repo"
        cmd = ["git", "clone", "--depth", "1"]
        if ref:
            cmd += ["--branch", ref]
        cmd += [url, str(tmp_repo)]
        try:
            subprocess.run(  # noqa: S603, S607
                cmd, check=True, capture_output=True, text=True, timeout=REMOTE_META_TIMEOUT,
            )
        except Exception:
            return {}
        target = tmp_repo / subpath if subpath else tmp_repo
        pp = target / "pyproject.toml"
        if not pp.exists():
            return {}
        return _read_plugin_meta(target)


def list_installed(plugins_dir: Path | None = None) -> list[dict]:
    """List installed plugins with their install manifest (version/source/url)."""
    plugins_dir = plugins_dir or get_plugins_dir()
    out = []
    if not plugins_dir.exists():
        return out
    for d in sorted(plugins_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        manifest = read_install_manifest(d)
        out.append({
            "name": d.name,
            "version": manifest.get("version"),
            "source": manifest.get("source", "unknown"),
            "url": manifest.get("url"),
            "subpath": manifest.get("subpath"),
            "ref": manifest.get("ref"),
            "installed_at": manifest.get("installed_at"),
        })
    return out


def check_update(name: str, plugins_dir: Path | None = None) -> dict:
    """Check if an installed plugin has a newer version available.

    Returns {name, local_version, remote_version, up_to_date}.
    Works for both registry and url/path-installed plugins: reads the local
    .pymss-install.json for the source url/subpath, fetches remote meta.
    """
    plugins_dir = plugins_dir or get_plugins_dir()
    dest = plugins_dir / name
    if not dest.exists():
        raise InstallError(f"no installed plugin named '{name}' in {plugins_dir}")
    manifest = read_install_manifest(dest)
    url = manifest.get("url")
    subpath = manifest.get("subpath")
    local_version = manifest.get("version")
    if not url:
        raise InstallError(
            f"plugin '{name}' has no url in its install manifest; cannot check for updates"
        )
    # Fetch remote meta from the default branch (no ref) so we detect new
    # releases even when the plugin was installed at a pinned ref.
    remote_meta = _fetch_remote_meta(url, subpath, ref=None)
    remote_version = remote_meta.get("version")
    return {
        "name": name,
        "local_version": local_version,
        "remote_version": remote_version,
        "up_to_date": (remote_version is None) or (local_version == remote_version),
    }


def update(name: str, plugins_dir: Path | None = None) -> InstallResult:
    """Reinstall a plugin at its latest version. Returns the new InstallResult.

    Ignores any pinned ref so the latest default-branch version is pulled.
    """
    plugins_dir = plugins_dir or get_plugins_dir()
    dest = plugins_dir / name
    if not dest.exists():
        raise InstallError(f"no installed plugin named '{name}' in {plugins_dir}")
    manifest = read_install_manifest(dest)
    url = manifest.get("url")
    subpath = manifest.get("subpath")
    source = manifest.get("source", "url")
    if not url:
        raise InstallError(
            f"plugin '{name}' has no url in its install manifest; cannot update"
        )
    # Reinstall via the original source, pulling the latest (ref=None).
    uninstall(name, plugins_dir=plugins_dir)
    if source == "path":
        return install(url, plugins_dir=plugins_dir, subpath=subpath)
    if source == "registry":
        return install(name, plugins_dir=plugins_dir, subpath=subpath)
    return install(url, plugins_dir=plugins_dir, subpath=subpath)


__all__ = [
    "InstallError",
    "InstallResult",
    "install",
    "uninstall",
    "list_available",
    "search_available",
    "list_installed",
    "check_update",
    "update",
    "read_install_manifest",
    "DEFAULT_REGISTRY_URL",
]
