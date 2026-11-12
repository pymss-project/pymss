from __future__ import annotations

import hashlib
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest

from pymss import model_download as download


@pytest.fixture
def model(monkeypatch, tmp_path):
    entry = SimpleNamespace(name="fixture", relpath="weights.ckpt", size_bytes=6)
    files = [(entry.relpath, tmp_path / entry.relpath), ("config.yaml", tmp_path / "config.yaml")]
    payloads = {"weights.ckpt": b"weight", "config.yaml": b"config"}
    monkeypatch.setattr(download, "files_for_model", lambda *_args: (entry, files))
    fetch = mock.Mock(side_effect=HTTPError(download.MS_FILES_API, 403, "Forbidden", None, None))
    monkeypatch.setattr(download, "fetch_modelscope_file_index", fetch)
    def transfer(_url, dest, *_args, **_kwargs):
        dest.write_bytes(payloads[dest.name])
    transfer = mock.Mock(side_effect=transfer)
    monkeypatch.setattr(download, "_download_file", transfer)
    return SimpleNamespace(entry=entry, files=files, payloads=payloads, fetch=fetch, transfer=transfer)


@pytest.mark.parametrize("source", ["modelscope", "huggingface", "hf-mirror"])
def test_complete_catalog_cache_needs_no_metadata_service(model, source):
    for _, dest in model.files:
        dest.write_bytes(model.payloads[dest.name])
    result = download.download_model("fixture", source=source)
    assert result["skipped"] == [str(dest) for _, dest in model.files]
    assert result["downloaded"] == []
    model.fetch.assert_not_called()
    model.transfer.assert_not_called()


@pytest.mark.parametrize("existing", [b"", b"short"])
def test_missing_metadata_cannot_certify_empty_or_truncated_weights(model, existing):
    model.files[0][1].write_bytes(existing)
    model.files[1][1].write_bytes(model.payloads["config.yaml"])
    result = download.download_model("fixture")
    assert result["downloaded"] == [str(model.files[0][1])]
    assert model.transfer.call_args.args[2] == len(model.payloads["weights.ckpt"])
    model.fetch.assert_called_once()


@pytest.mark.parametrize("empty", [False, True])
def test_missing_or_empty_secondary_file_is_downloaded_after_metadata_403(model, empty):
    model.files[0][1].write_bytes(model.payloads["weights.ckpt"])
    if empty:
        model.files[1][1].touch()
    result = download.download_model("fixture")
    assert result["downloaded"] == [str(model.files[1][1])]
    assert result["skipped"] == [str(model.files[0][1])]


@pytest.mark.parametrize("source", ["huggingface", "hf-mirror"])
def test_other_sources_never_require_modelscope_metadata(model, source):
    result = download.download_model("fixture", source=source)
    assert len(result["downloaded"]) == 2
    model.fetch.assert_not_called()


def test_available_index_keeps_published_hash_validation(model):
    model.files[0][1].write_bytes(b"broken")
    model.fetch.side_effect = None
    model.fetch.return_value = {"weights.ckpt": {
        "Size": 6, "Sha256": hashlib.sha256(model.payloads["weights.ckpt"]).hexdigest(),
    }}
    result = download.download_model("fixture")
    assert str(model.files[0][1]) in result["downloaded"]
    assert model.transfer.call_args_list[0].args[3] == model.fetch.return_value["weights.ckpt"]["Sha256"]


def test_force_still_downloads_every_file(model):
    for _, dest in model.files:
        dest.write_bytes(model.payloads[dest.name])
    result = download.download_model("fixture", force=True)
    assert len(result["downloaded"]) == 2
    model.fetch.assert_called_once()


@pytest.mark.parametrize("options", [{"verify": False}, {"endpoint": "https://custom.invalid"}])
def test_explicit_unverified_modes_keep_their_no_index_behavior(model, options):
    for _, dest in model.files:
        dest.write_bytes(b"custom")
    result = download.download_model("fixture", **options)
    assert len(result["skipped"]) == 2
    model.fetch.assert_not_called()
    model.transfer.assert_not_called()


def test_unknown_cached_weights_are_downloaded_instead_of_certified(model):
    model.entry.size_bytes = 0
    model.files[0][1].write_bytes(b"truncated")
    result = download.download_model("fixture")
    assert str(model.files[0][1]) in result["downloaded"]


def test_file_download_failure_is_not_hidden_by_optional_metadata(model):
    model.transfer.side_effect = URLError("file transfer failed")
    with pytest.raises(URLError, match="file transfer failed"):
        download.download_model("fixture")


def test_invalid_proxy_is_not_treated_as_a_metadata_outage(model):
    model.fetch.side_effect = download.ProxyError("invalid proxy")
    with pytest.raises(download.ProxyError, match="invalid proxy"):
        download.download_model("fixture")
    model.transfer.assert_not_called()


def test_empty_file_is_never_valid_without_metadata(tmp_path):
    path = tmp_path / "weights.ckpt"
    path.touch()
    assert not download._already_valid(path)


def test_empty_download_is_not_accepted_without_metadata(tmp_path):
    partial = tmp_path / "config.yaml.part"
    partial.touch()
    with pytest.raises(download.DownloadValidationError, match="empty download"):
        download._validate_downloaded_file(partial, tmp_path / "config.yaml")


def test_catalog_hash_still_rejects_same_size_corruption_during_outage(model):
    model.entry.sha256 = hashlib.sha256(model.payloads["weights.ckpt"]).hexdigest()
    model.files[0][1].write_bytes(b"broken")
    model.files[1][1].write_bytes(model.payloads["config.yaml"])
    result = download.download_model("fixture")
    assert result["downloaded"] == [str(model.files[0][1])]
    assert model.transfer.call_args.args[3] == model.entry.sha256
