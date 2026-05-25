import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from tqdm import tqdm

from .model_registry import (
    auxiliary_paths_for,
    config_path_for,
    get_model_entry,
    model_path_for,
    model_root,
)


HF_REPO = "baicai1145/pymss"
MS_REPO = "baicai1145/pymss"
HF_BASE_URL = f"https://huggingface.co/{HF_REPO}/resolve/main"
MS_BASE_URL = f"https://www.modelscope.cn/models/{MS_REPO}/resolve/master"
MS_FILES_API = f"https://www.modelscope.cn/api/v1/models/{MS_REPO}/repo/files?Revision=master&Recursive=true"
MODEL_FILE_SUFFIXES = {".ckpt", ".th", ".pth", ".chpt", ".safetensors", ".pt", ".yaml", ".yml", ".json"}


class DownloadError(RuntimeError):
    pass


def _quote_path(path):
    return urllib.parse.quote(path, safe="/")


def remote_url(relpath, source="modelscope", endpoint=None):
    if endpoint:
        return f"{endpoint.rstrip('/')}/{_quote_path(relpath)}"
    if source == "huggingface":
        return f"{HF_BASE_URL}/{_quote_path(relpath)}"
    if source == "hf-mirror":
        return f"https://hf-mirror.com/{HF_REPO}/resolve/main/{_quote_path(relpath)}"
    if source == "modelscope":
        return f"{MS_BASE_URL}/{_quote_path(relpath)}"
    raise ValueError("source must be one of: modelscope, huggingface, hf-mirror")


def _read_json_url(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def fetch_modelscope_file_index(timeout=30):
    data = _read_json_url(MS_FILES_API, timeout=timeout)
    files = data.get("Data", {}).get("Files", [])
    return {
        item["Path"]: item
        for item in files
        if item.get("Type") == "blob"
    }


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _expected_size_and_hash(relpath, source_index):
    if not source_index:
        return None, ""
    item = source_index.get(relpath, {})
    size = item.get("Size")
    sha256 = item.get("Sha256") or ""
    return int(size) if size else None, sha256


def _already_valid(path, expected_size=None, expected_sha256=""):
    if not path.is_file():
        return False
    if expected_size is not None and path.stat().st_size != expected_size:
        return False
    if expected_sha256 and _sha256(path) != expected_sha256:
        return False
    return True


def _download_file(url, dest, expected_size=None, expected_sha256="", timeout=30, retries=2):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    last_error = None

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                total = int(response.headers.get("content-length") or expected_size or 0)
                with open(tmp, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as progress:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        progress.update(len(chunk))
            if expected_size is not None and tmp.stat().st_size != expected_size:
                raise DownloadError(f"size mismatch for {dest.name}: expected {expected_size}, got {tmp.stat().st_size}")
            if expected_sha256:
                actual = _sha256(tmp)
                if actual != expected_sha256:
                    raise DownloadError(f"sha256 mismatch for {dest.name}: expected {expected_sha256}, got {actual}")
            os.replace(tmp, dest)
            return dest
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, DownloadError) as exc:
            last_error = exc
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
            if attempt < retries:
                time.sleep(1.0 + attempt)
    raise DownloadError(f"failed to download {url}: {last_error}")


def files_for_model(model_name, model_dir=None):
    entry = get_model_entry(model_name)
    files = [(entry.relpath, model_path_for(entry, model_dir))]
    config_path = config_path_for(entry, model_dir)
    if entry.config_relpath and config_path is not None:
        files.append((entry.config_relpath, config_path))
    files.extend(zip(entry.auxiliary_relpaths, auxiliary_paths_for(entry, model_dir)))
    return entry, files


def download_model(model_name, model_dir=None, source="modelscope", endpoint=None, verify=True, force=False, timeout=30):
    entry, files = files_for_model(model_name, model_dir)
    index = fetch_modelscope_file_index(timeout=timeout) if verify and endpoint is None else None
    downloaded = []
    skipped = []

    for relpath, dest in files:
        expected_size, expected_sha256 = _expected_size_and_hash(relpath, index)
        if not force and _already_valid(dest, expected_size, expected_sha256):
            skipped.append(str(dest))
            continue
        url = remote_url(relpath, source=source, endpoint=endpoint)
        _download_file(url, dest, expected_size, expected_sha256, timeout=timeout)
        downloaded.append(str(dest))

    return {"entry": entry, "downloaded": downloaded, "skipped": skipped, "model_dir": str(model_root(model_dir))}


def download_all(model_dir=None, source="modelscope", endpoint=None, supported_only=False, force=False, timeout=30):
    from .model_registry import list_models

    results = []
    for entry in list_models(supported=True if supported_only else None):
        try:
            results.append(download_model(entry.name, model_dir=model_dir, source=source, endpoint=endpoint, force=force, timeout=timeout))
        except Exception as exc:
            results.append({"entry": entry, "error": str(exc)})
    return results
