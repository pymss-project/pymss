"""Tests for the unified DAG core, comfy_loader, yaml_to_dag, and the
folder-batched LegacyWorkflowRunner.

These mirror the assertions in ``test_workflow.py`` so that the DAG-backed
runner is held to the same output-layout contract as the legacy runner, plus
they exercise the comfy-mss JSON loading path against every example graph.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from pymss.comfy_loader import load_comfy_file, load_comfy_graph
from pymss.dag import (
    DAG,
    DAGError,
    DAGNode,
    SeparatorCache,
    run_dag,
    topological_order,
)
from pymss.workflow import load_workflow_data
from pymss.workflow_runner import LegacyWorkflowRunner
from pymss.yaml_to_dag import compile_workflow_to_dag


COMFY_EXAMPLES_DIR = Path("/Volumes/data/comfy-mss/examples")


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


class FakeSeparator:
    """Stand-in separator that records calls and returns deterministic stems.

    Mirrors the FakeSeparator in test_workflow.py so the two runners can be
    compared directly.
    """

    def __init__(self, model_name: str, calls: list, sample_rate: int = 44100):
        self.model_name = model_name
        self.calls = calls
        self.model_type = "fake"
        self.device = "cpu"
        self.audio_params: dict[str, Any] = {}
        self.config = SimpleNamespace(
            training=SimpleNamespace(instruments=["vocals", "other", "Dry"], target_instrument=None),
            audio={"sample_rate": sample_rate},
            inference={"batch_size": 1},
        )
        self.progress_callback = None

    def separate(self, mix, pbar=False, stems=None):
        self.calls.append((self.model_name, np.asarray(mix).shape, tuple(stems) if stems else None))
        base = np.asarray(mix, dtype=np.float32)
        # pymss separators hand back [samples, channels]; emulate that so the
        # DAG's audio helpers transpose it the same way they do real outputs.
        save_major = base.T if base.ndim == 2 and base.shape[0] in (1, 2) else base
        requested = list(stems or self.config.training.instruments)
        return {stem: save_major + (index + 1) for index, stem in enumerate(requested)}

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_factory(calls):
    def _factory(model_name, **_kwargs):
        return FakeSeparator(model_name, calls)
    return _factory


def _stub_audio_io(monkeypatch, captures):
    """Replace load_audio/save_audio with in-memory stubs."""

    def _load(path, sr=None, mono=False, offset=0.0, duration=None):
        return np.asarray([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32), 44100

    def _save(path, audio, sr, output_format, audio_params):
        captures.append((path, np.asarray(audio).copy(), sr, output_format))

    import pymss.audio_io as audio_io

    monkeypatch.setattr(audio_io, "load_audio", _load)
    monkeypatch.setattr(audio_io, "save_audio", _save)


# ---------------------------------------------------------------------------
# Topological ordering
# ---------------------------------------------------------------------------


def _node(node_id, type="mss_separate", inputs=None):
    return DAGNode(id=node_id, type=type, inputs=list(inputs or []))


def test_topological_order_respects_dependencies():
    # 3 -> 2 -> 1 (declared out of order)
    n1 = _node(1)
    n2 = _node(2)
    n3 = _node(3)
    from pymss.dag import DAGLink

    n2.inputs = [DAGLink(link_id=1, source_node_id=n3.id, source_slot=0, target_node_id=n2.id, target_slot=0, type="AUDIO")]
    n1.inputs = [DAGLink(link_id=2, source_node_id=n2.id, source_slot=0, target_node_id=n1.id, target_slot=0, type="AUDIO")]
    order = topological_order([n1, n2, n3])
    assert [n.id for n in order] == [3, 2, 1]


def test_topological_order_detects_cycle():
    from pymss.dag import DAGLink

    a = _node("a")
    b = _node("b")
    a.inputs = [DAGLink(link_id=1, source_node_id="b", source_slot=0, target_node_id="a", target_slot=0, type="AUDIO")]
    b.inputs = [DAGLink(link_id=2, source_node_id="a", source_slot=0, target_node_id="b", target_slot=0, type="AUDIO")]
    with pytest.raises(DAGError, match="cycle"):
        topological_order([a, b])


def test_topological_order_rejects_dangling_link():
    from pymss.dag import DAGLink

    n = _node("x")
    n.inputs = [DAGLink(link_id=1, source_node_id="missing", source_slot=0, target_node_id="x", target_slot=0, type="AUDIO")]
    with pytest.raises(DAGError, match="unknown source node"):
        topological_order([n])


# ---------------------------------------------------------------------------
# comfy_loader: every example parses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("example", sorted(glob.glob(str(COMFY_EXAMPLES_DIR / "*.json"))) or [])
def test_comfy_loader_parses_every_example(example):
    dag = load_comfy_file(example)
    assert dag.nodes
    types = {n.type for n in dag.nodes}
    # Every example must contain at least one comfy-mss node we recognize.
    recognized = types & {
        "mss_separate", "mss_separate_list", "vr_separate", "vr_separate_list",
        "custom_mss_separate", "custom_mss_separate_list",
        "pymss_audio_ensemble", "pymss_audio_invert_phase", "pymss_audio_normalize",
    }
    assert recognized, f"{example} has no recognized comfy-mss nodes: {types}"


def test_comfy_loader_rejects_non_object():
    with pytest.raises(DAGError):
        load_comfy_graph([1, 2, 3])


def test_comfy_loader_strict_unknown_node_raises(tmp_path):
    graph = {
        "nodes": [
            {"id": 1, "type": "pymss_load_audio", "widgets_values": ["x.wav"], "outputs": []},
            {"id": 2, "type": "totally_made_up", "widgets_values": [], "inputs": [], "outputs": []},
        ],
        "links": [],
    }
    dag = load_comfy_graph(graph)
    # Loading succeeds (we keep unknown nodes in the graph); running strict fails.
    with pytest.raises(Exception):
        run_dag(dag, output_dir=tmp_path, input_path="x.wav", strict=True)


# ---------------------------------------------------------------------------
# yaml_to_dag: compilation correctness
# ---------------------------------------------------------------------------


def test_yaml_compiles_two_step_chain_with_correct_slots():
    workflow = load_workflow_data({
        "version": 1,
        "steps": [
            {"id": "split", "model": "m1", "input": "input", "stems": ["vocals", "other"], "save": {"vocals": "vocal", "other": "other"}},
            {"id": "dereverb", "model": "m2", "input": "split.other", "stems": ["Dry"], "save": {"Dry": "dry"}},
        ],
    })
    dag = compile_workflow_to_dag(workflow)
    ids = [n.id for n in dag.nodes]
    assert "input" in ids
    assert "step:split" in ids and "step:dereverb" in ids
    # dereverb's audio input must come from split's "other" stem, which is slot 2
    # (vocals=0 audio, vocals=1 string, other=2 audio).
    dereverb = dag.node("step:dereverb")
    assert dereverb.inputs[0] is not None
    assert dereverb.inputs[0].source_node_id == "step:split"
    assert dereverb.inputs[0].source_slot == 2


def test_yaml_compile_rejects_unknown_upstream_step():
    # ``load_workflow_data`` does NOT eagerly validate cross-step references;
    # that check runs inside ``validate_workflow`` (called by the compiler).
    workflow = load_workflow_data({
        "version": 1,
        "steps": [
            {"id": "s", "model": "m", "input": "ghost.stem", "stems": ["vocals"], "save": {"vocals": "v"}},
        ],
    })
    with pytest.raises(Exception, match="unknown step"):
        compile_workflow_to_dag(workflow)


# ---------------------------------------------------------------------------
# LegacyWorkflowRunner: output layout matches the legacy contract
# ---------------------------------------------------------------------------


def test_legacy_runner_produces_per_track_outputs(monkeypatch, tmp_path):
    workflow = load_workflow_data({
        "version": 1,
        "steps": [
            {"id": "split", "model": "split-model", "input": "input", "stems": ["vocals", "other"], "save": {"vocals": "vocal", "other": "other"}},
            {"id": "dereverb", "model": "dereverb-model", "input": "split.other", "stems": ["Dry"], "save": {"Dry": "dry"}},
        ],
    })
    calls: list = []
    captures: list = []
    _stub_audio_io(monkeypatch, captures)
    (tmp_path / "song.wav").write_bytes(b"fake")

    runner = LegacyWorkflowRunner(workflow, separator_factory=_fake_factory(calls))
    processed = runner.run(str(tmp_path / "song.wav"), tmp_path)

    assert processed == ["song.wav"]
    paths = sorted(Path(c[0]).relative_to(tmp_path).as_posix() for c in captures)
    assert paths == [
        "song/dry/song_Dry.wav",
        "song/other/song_other.wav",
        "song/vocal/song_vocals.wav",
    ]
    # Two separators loaded once each (cache shared within the single-file run).
    assert [c[0] for c in calls] == ["split-model", "dereverb-model"]


def test_legacy_runner_flat_layout(monkeypatch, tmp_path):
    workflow = load_workflow_data({
        "version": 1,
        "steps": [
            {"id": "split", "model": "m", "input": "input", "stems": ["vocals"], "save": {"vocals": "vocal"}},
        ],
    })
    captures: list = []
    _stub_audio_io(monkeypatch, captures)
    (tmp_path / "song.wav").write_bytes(b"fake")

    runner = LegacyWorkflowRunner(workflow, output_layout="flat", separator_factory=_fake_factory([]))
    runner.run(str(tmp_path / "song.wav"), tmp_path)
    rel = Path(captures[0][0]).relative_to(tmp_path).as_posix()
    assert rel == "vocal/song_vocals.wav"


def test_legacy_runner_batches_folder_with_shared_cache(monkeypatch, tmp_path):
    workflow = load_workflow_data({
        "version": 1,
        "steps": [
            {"id": "s", "model": "m", "input": "input", "stems": ["vocals"], "save": {"vocals": "vocal"}},
        ],
    })
    calls: list = []
    captures: list = []
    _stub_audio_io(monkeypatch, captures)
    (tmp_path / "a.wav").write_bytes(b"x")
    (tmp_path / "b.wav").write_bytes(b"x")

    runner = LegacyWorkflowRunner(workflow, separator_factory=_fake_factory(calls))
    processed = runner.run(str(tmp_path), tmp_path)

    assert sorted(processed) == ["a.wav", "b.wav"]
    # Same model loaded once for both files.
    assert [c[0] for c in calls] == ["m", "m"]


# ---------------------------------------------------------------------------
# Comfy JSON end-to-end (with a fake separator factory wired through the cache)
# ---------------------------------------------------------------------------


def test_comfy_run_end_to_end_with_fake_separator(monkeypatch, tmp_path):
    """example_mss_separate.json wires load -> separate -> save; run it with fakes."""

    dag = load_comfy_file(COMFY_EXAMPLES_DIR / "example_mss_separate.json")
    calls: list = []
    captures: list = []
    _stub_audio_io(monkeypatch, captures)

    cache = SeparatorCache(factory=lambda **kw: FakeSeparator(kw.get("model_name", "?"), calls))
    saved = run_dag(
        dag,
        output_dir=tmp_path,
        input_path="input.wav",
        separator_cache=cache,
        download=False,
    )
    cache.close()

    assert saved, "comfy graph should have written at least one file"
    # example_mss_separate wires filename = "input" + "_" + stem via StringConcatenate,
    # so saved names are input_other / input_vocals. Assert both stems landed.
    stems = sorted(Path(p).stem for p in saved)
    assert "input_other" in stems and "input_vocals" in stems
    assert len(calls) == 1, "single mss_separate node runs the model once"


# ---------------------------------------------------------------------------
# Composite graph: load -> separate -> (invert + direct) -> ensemble -> save
# ---------------------------------------------------------------------------


def test_dag_runs_ensemble_of_inverted_and_direct_stem(monkeypatch, tmp_path):
    """avg(vocals, -other) over a deterministic fake model should be ~0.1."""

    from pymss.dag import DAGLink

    def _load(path, sr=None, mono=False, **_kw):
        return np.asarray([[0.5, 0.4, 0.3], [0.2, 0.1, 0.0]], dtype=np.float32), 44100

    saved: list = []

    def _save(path, audio, sr, fmt, ap):
        saved.append((path, np.asarray(audio).copy()))

    import pymss.audio_io as audio_io

    monkeypatch.setattr(audio_io, "load_audio", _load)
    monkeypatch.setattr(audio_io, "save_audio", _save)

    def factory(**kw):
        sep = FakeSeparator(kw.get("model_name", "?"), [])
        # Override separate to return vocals/+0.1, other/-0.1 around the mix.
        def _separate(mix, pbar=False, stems=None):
            base = np.asarray(mix, dtype=np.float32)
            sm = base.T if base.ndim == 2 and base.shape[0] in (1, 2) else base
            return {"vocals": sm + 0.1, "other": sm - 0.1}
        sep.separate = _separate
        return sep

    def lk(pool, snode, sslot, tnode, tslot):
        return DAGLink(link_id=len(pool) + 1, source_node_id=snode, source_slot=sslot, target_node_id=tnode, target_slot=tslot, type="AUDIO")

    pool: list = []
    nodes = [
        DAGNode(id=1, type="pymss_load_audio", inputs=[], data={"widgets_values": ["x.wav"], "outputs": []}),
        DAGNode(id=4, type="pymss_audio_invert_phase", inputs=[None], data={"widgets_values": []}),
        DAGNode(id=2, type="mss_separate", inputs=[None, None], data={
            "widgets_values": ["m", "auto", True, "modelscope", "0", False],
            "outputs": [
                {"name": "vocals (Audio)", "type": "AUDIO"},
                {"name": "vocals (String)", "type": "STRING"},
                {"name": "other (Audio)", "type": "AUDIO"},
                {"name": "other (String)", "type": "STRING"},
            ],
        }),
        DAGNode(id=3, type="pymss_audio_ensemble", inputs=[None, None], data={"widgets_values": [2, "avg_wave", 1, 1]}),
        DAGNode(id=5, type="pymss_save_audio", inputs=[None] * 8, data={"widgets_values": ["wav", "out", "44100", "FLOAT", "PCM_24", "320k"]}),
    ]
    nodes[2].inputs[0] = lk(pool, 1, 0, 2, 0)
    nodes[1].inputs[0] = lk(pool, 2, 2, 4, 0)
    nodes[3].inputs[0] = lk(pool, 2, 0, 3, 0)
    nodes[3].inputs[1] = lk(pool, 4, 0, 3, 1)
    nodes[4].inputs[0] = lk(pool, 3, 0, 5, 0)

    cache = SeparatorCache(factory=factory)
    run_dag(DAG(nodes=nodes), output_dir=tmp_path, input_path="x.wav", separator_cache=cache, download=False)
    cache.close()

    assert saved, "ensemble graph should have saved one file"
    # avg(mix + 0.1, -(mix - 0.1)) = 0.1 regardless of the mix values.
    assert np.allclose(saved[0][1], 0.1, atol=1e-5)
