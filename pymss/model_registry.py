import json
import os
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path


def _default_model_dir():
    env_value = os.environ.get("PYMSS_MODEL_DIR")
    if env_value:
        return Path(env_value)
    repo_models = Path(__file__).resolve().parent.parent / "all_models"
    if repo_models.is_dir():
        return repo_models
    return Path.home() / ".cache" / "pymss" / "models"


DEFAULT_MODEL_DIR = _default_model_dir()


@dataclass(frozen=True)
class ModelEntry:
    name: str
    aliases: tuple
    model_type: str | None
    architecture: str
    supported: bool
    unsupported_reason: str
    relpath: str
    config_relpath: str
    auxiliary_relpaths: tuple
    size_bytes: int
    sha256: str
    primary_category: str
    primary_category_cn: str
    secondary_category: str
    secondary_category_cn: str
    target_stem: str
    config_instruments: str
    config_target_instrument: str
    classification_confidence: str
    classification_basis: str

    @property
    def stem(self):
        return Path(self.name).stem

    @property
    def category_path(self):
        return "/".join(part for part in (self.primary_category, self.secondary_category) if part)

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            aliases=tuple(data.get("aliases", ())),
            model_type=data.get("model_type"),
            architecture=data.get("architecture", ""),
            supported=bool(data.get("supported", False)),
            unsupported_reason=data.get("unsupported_reason", ""),
            relpath=data["relpath"],
            config_relpath=data.get("config_relpath", ""),
            auxiliary_relpaths=tuple(data.get("auxiliary_relpaths", ())),
            size_bytes=int(data.get("size_bytes", 0)),
            sha256=data.get("sha256", ""),
            primary_category=data.get("primary_category", ""),
            primary_category_cn=data.get("primary_category_cn", ""),
            secondary_category=data.get("secondary_category", ""),
            secondary_category_cn=data.get("secondary_category_cn", ""),
            target_stem=data.get("target_stem", ""),
            config_instruments=data.get("config_instruments", ""),
            config_target_instrument=data.get("config_target_instrument", ""),
            classification_confidence=data.get("classification_confidence", ""),
            classification_basis=data.get("classification_basis", ""),
        )


@lru_cache(maxsize=1)
def load_model_catalog():
    with resources.files("pymss.resources").joinpath("model_catalog.json").open(encoding="utf-8") as f:
        data = json.load(f)
    models = [ModelEntry.from_dict(item) for item in data["models"]]
    return {**data, "models": models}


@lru_cache(maxsize=1)
def _model_index():
    index = {}
    for entry in load_model_catalog()["models"]:
        names = {entry.name, entry.stem, *entry.aliases}
        for name in names:
            key = _normalize_model_name(name)
            if key in index and index[key].name != entry.name:
                continue
            index[key] = entry
    return index


def _normalize_model_name(name):
    return str(name).strip().lower()


def list_models(category=None, supported=None):
    models = load_model_catalog()["models"]
    if category:
        category = category.lower()
        models = [
            item for item in models
            if item.primary_category.lower() == category
            or item.secondary_category.lower() == category
            or item.category_path.lower() == category
        ]
    if supported is not None:
        models = [item for item in models if item.supported is bool(supported)]
    return models


def get_model_entry(model_name):
    try:
        return _model_index()[_normalize_model_name(model_name)]
    except KeyError as exc:
        raise KeyError(f"Unknown pymss model: {model_name}") from exc


def model_root(model_dir=None):
    return Path(model_dir).expanduser() if model_dir else DEFAULT_MODEL_DIR


def model_path_for(entry, model_dir=None):
    return model_root(model_dir) / entry.relpath


def config_path_for(entry, model_dir=None):
    return model_root(model_dir) / entry.config_relpath if entry.config_relpath else None


def auxiliary_paths_for(entry, model_dir=None):
    root = model_root(model_dir)
    return [root / relpath for relpath in entry.auxiliary_relpaths]


def resolve_model(model_name, model_dir=None, require_supported=True, require_exists=True):
    entry = get_model_entry(model_name)
    if require_supported and not entry.supported:
        reason = entry.unsupported_reason or "unsupported"
        raise ValueError(f"Model {entry.name} cannot be used for inference yet: {reason}")

    model_path = model_path_for(entry, model_dir)
    config_path = config_path_for(entry, model_dir)
    missing = []
    if require_exists and not model_path.is_file():
        missing.append(str(model_path))
    if require_exists and config_path is not None and not config_path.is_file():
        missing.append(str(config_path))
    for path in auxiliary_paths_for(entry, model_dir):
        if require_exists and not path.is_file():
            missing.append(str(path))
    if missing:
        raise FileNotFoundError("Missing model file(s): " + ", ".join(missing))

    return {
        "entry": entry,
        "model_type": entry.model_type,
        "model_path": str(model_path),
        "config_path": str(config_path) if config_path else None,
    }


def create_separator(model_name, model_dir=None, **separator_kwargs):
    from .separator import MSSeparator

    resolved = resolve_model(model_name, model_dir=model_dir, require_supported=True, require_exists=True)
    return MSSeparator(
        model_type=resolved["model_type"],
        model_path=resolved["model_path"],
        config_path=resolved["config_path"],
        **separator_kwargs,
    )
