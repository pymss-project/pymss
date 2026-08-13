"""Tests for the plugin system: registration API, folder-scan loading, install/uninstall."""

from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

import pytest

from pymss.plugins import (
    CapabilityNotFound,
    bootstrap,
    get_plugins_dir,
    get_registry,
    register_capability,
    register_cli,
    register_node,
    require_capability,
    reset,
)
from pymss.plugins.install import InstallError, install, uninstall


# ---------------------------------------------------------------------------
# Registration API
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_registry():
    """Each test starts with a clean registry and loader cache."""
    reg = get_registry()
    reg.capabilities.clear()
    reg.nodes.clear()
    reg.cli_commands.clear()
    reg._reserved_node_types.clear()
    reset()
    yield
    reg.capabilities.clear()
    reg.nodes.clear()
    reg.cli_commands.clear()
    reg._reserved_node_types.clear()
    reset()


def test_register_capability_direct():
    def fn(x):
        return x + 1

    register_capability("inc", fn, source="test")
    assert require_capability("inc")(1) == 2


def test_register_capability_decorator():
    @register_capability("double")
    def double(x):
        return x * 2

    assert double(3) == 6  # decorator returns the original func
    assert require_capability("double")(3) == 6


def test_require_capability_missing_raises():
    with pytest.raises(CapabilityNotFound) as exc_info:
        require_capability("nope")
    assert "nope" in str(exc_info.value)


def test_register_node():
    @register_node("MyPluginNode")
    def handler(ctx, inputs):
        return {"out": "ok"}

    reg = get_registry()
    assert reg.get_node("MyPluginNode") is handler


def test_reserved_node_cannot_be_overridden_by_plugin():
    reg = get_registry()
    reg.reserve_node_type("mss_separate")

    with pytest.raises(ValueError, match="reserved"):
        register_node("mss_separate", lambda ctx, inputs: None, source="evil")


def test_reserved_node_allows_builtin_override():
    reg = get_registry()
    reg.reserve_node_type("mss_separate")
    # pymss core itself can register reserved nodes with the internal flag.
    reg.register_node(
        "mss_separate", lambda ctx, inputs: None, source="builtin", allow_override_builtin=True
    )
    assert reg.get_node("mss_separate") is not None


def test_register_cli_parses_path():
    register_cli("opus encode", lambda args: 0, help="encode opus")
    reg = get_registry()
    assert len(reg.cli_commands) == 1
    assert reg.cli_commands[0].path == ("opus", "encode")


# ---------------------------------------------------------------------------
# Folder-scan loading
# ---------------------------------------------------------------------------


def _make_plugin_dir(plugins_dir: Path, name: str, body: str) -> Path:
    d = plugins_dir / name
    d.mkdir(parents=True)
    (d / "__init__.py").write_text(textwrap.dedent(body))
    return d


def test_folder_scan_loads_plugin(tmp_path, monkeypatch):
    plugins_dir = tmp_path / "plugins"
    _make_plugin_dir(
        plugins_dir,
        "myplug",
        """
        from pymss.plugins import register_capability
        register_capability("myplug_thing", lambda x: x * 10, source="myplug")
        """,
    )
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(plugins_dir))
    reset()

    report = bootstrap()
    assert report.bootstrapped
    assert "myplug" in report.loaded_names
    assert require_capability("myplug_thing")(5) == 50


def test_folder_scan_isolates_failures(tmp_path, monkeypatch):
    plugins_dir = tmp_path / "plugins"
    # good plugin
    _make_plugin_dir(
        plugins_dir,
        "good",
        """
        from pymss.plugins import register_capability
        register_capability("good_cap", lambda: 1, source="good")
        """,
    )
    # bad plugin (ImportError)
    bad = plugins_dir / "bad"
    bad.mkdir()
    (bad / "__init__.py").write_text("raise RuntimeError('boom')\n")
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(plugins_dir))
    reset()

    report = bootstrap()
    assert "good" in report.loaded_names
    failed = {r.name: r for r in report.failed}
    assert "bad" in failed
    assert "boom" in failed["bad"].error
    # good plugin's capability still registered despite bad plugin failing
    assert require_capability("good_cap")() == 1


def test_bootstrap_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(tmp_path / "empty"))
    reset()
    r1 = bootstrap()
    r2 = bootstrap()
    assert r1 is r2
    r3 = bootstrap(force=True)
    assert r3 is not r1


def test_get_plugins_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(tmp_path / "custom"))
    assert get_plugins_dir() == tmp_path / "custom"


def test_get_plugins_dir_default(monkeypatch):
    monkeypatch.delenv("PYMSS_PLUGINS_DIR", raising=False)
    from pymss.plugins.loader import DEFAULT_PLUGINS_DIR

    assert get_plugins_dir() == DEFAULT_PLUGINS_DIR


# ---------------------------------------------------------------------------
# Install / uninstall
# ---------------------------------------------------------------------------


def test_install_from_local_path(tmp_path, monkeypatch):
    plugins_dir = tmp_path / "installed"
    # source plugin
    src = tmp_path / "src" / "myplugin"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text(
        "from pymss.plugins import register_capability\n"
        "register_capability('copied_cap', lambda: 42, source='myplugin')\n"
    )
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(plugins_dir))

    result = install(str(src))
    assert result.source == "path"
    assert result.name == "myplugin"
    assert (plugins_dir / "myplugin" / "__init__.py").exists()

    # The copied plugin loads correctly.
    reset()
    bootstrap()
    assert require_capability("copied_cap")() == 42


def test_install_duplicate_raises(tmp_path, monkeypatch):
    plugins_dir = tmp_path / "installed"
    src = tmp_path / "src" / "dup"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(plugins_dir))

    install(str(src))
    with pytest.raises(InstallError, match="already exists"):
        install(str(src))


def test_uninstall_removes_dir(tmp_path, monkeypatch):
    plugins_dir = tmp_path / "installed"
    src = tmp_path / "src" / "gone"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(plugins_dir))

    install(str(src))
    dest = plugins_dir / "gone"
    assert dest.exists()
    removed = uninstall("gone")
    assert removed == dest
    assert not dest.exists()


def test_uninstall_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(tmp_path / "empty"))
    with pytest.raises(InstallError, match="no installed plugin"):
        uninstall("ghost")


def test_install_unknown_name_without_registry_raises(tmp_path, monkeypatch):
    # Point registry at a non-existent URL so the fetch fails fast.
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(tmp_path / "p"))
    monkeypatch.setenv("PYMSS_PLUGINS_REGISTRY", "http://127.0.0.1:1/nope.json")
    with pytest.raises(InstallError, match="registry|URL|path|fetch"):
        install("nonexistent-plugin-name")


# ---------------------------------------------------------------------------
# CLI smoke (argparse wiring)
# ---------------------------------------------------------------------------


def test_cli_install_and_plugins_list(tmp_path, monkeypatch):
    from pymss.cli import main

    plugins_dir = tmp_path / "cli_plugins"
    monkeypatch.setenv("PYMSS_PLUGINS_DIR", str(plugins_dir))
    reset()

    src = tmp_path / "src" / "clipplug"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text(
        "from pymss.plugins import register_capability\n"
        "register_capability('cli_cap', lambda: 7, source='clipplug')\n"
    )

    # install
    rc = main(["install", str(src)])
    assert rc == 0

    # plugins list (bootstrap loads the freshly installed plugin)
    reset()
    rc = main(["plugins", "list"])
    assert rc == 0

    # plugins dir
    rc = main(["plugins", "dir"])
    assert rc == 0
