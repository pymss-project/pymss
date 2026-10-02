import logging
from unittest.mock import patch

import numpy as np
import pytest

from pymss.config import AttrDict
from pymss.model_registry import create_separator, get_model_entry, resolve_model
from pymss.separator import (
    MSSeparator,
    _apply_target_instrument_override,
    _build_results,
    _catalog_target_instrument_override,
)


MODEL_NAME = "model_mel_band_roformer_ep_0_sdr_11.4805.ckpt"


def test_issue_64_catalog_entry_corrects_the_reported_stem_order():
    entry = get_model_entry(MODEL_NAME)
    assert entry.category_path == "vocal/vocal_extraction"
    assert entry.target_stem == "Vocals"
    assert entry.target_instrument_override == "Vocals"

    resolved = resolve_model(MODEL_NAME, require_exists=False)
    assert resolved["target_instrument_override"] == "Vocals"


def test_target_instrument_override_uses_the_configured_stem_casing():
    config = AttrDict(
        {
            "training": {
                "instruments": ["Vocals", "Instrumental"],
                "target_instrument": "Instrumental",
            },
        }
    )

    _apply_target_instrument_override(config, "vocals")

    assert config.training.target_instrument == "Vocals"


def test_target_instrument_override_rejects_unknown_stems():
    config = AttrDict(
        {
            "training": {
                "instruments": ["Vocals", "Instrumental"],
                "target_instrument": "Instrumental",
            },
        }
    )

    with pytest.raises(ValueError, match="is not present in configured instruments"):
        _apply_target_instrument_override(config, "Other")


def test_explicit_catalog_model_paths_pick_up_the_override():
    assert _catalog_target_instrument_override(f"models/{MODEL_NAME}") == "Vocals"
    assert _catalog_target_instrument_override("models/custom.ckpt") is None


def test_corrected_target_labels_the_prediction_as_vocals_and_residual_as_instrumental():
    config = AttrDict(
        {
            "training": {
                "instruments": ["Vocals", "Instrumental"],
                "target_instrument": "Instrumental",
            },
        }
    )
    mix = np.array([[0.8, -0.4]], dtype=np.float32)
    predicted = np.array([[0.3, -0.1]], dtype=np.float32)

    _apply_target_instrument_override(config, "Vocals")
    results = _build_results(
        {"Vocals": predicted},
        config.training.instruments,
        mix,
        config,
        None,
        logging.getLogger(__name__),
    )

    np.testing.assert_allclose(results["Vocals"], predicted.T)
    np.testing.assert_allclose(results["Instrumental"], (mix - predicted).T)


def test_create_separator_forwards_catalog_target_override():
    resolved = {
        "model_type": "mel_band_roformer",
        "model_path": "model.ckpt",
        "config_path": "model.yaml",
        "source": "catalog",
        "inference_params": {},
        "target_instrument_override": "Vocals",
    }
    sentinel = object()
    with (
        patch("pymss.model_registry.resolve_model", return_value=resolved),
        patch("pymss.separator.MSSeparator", return_value=sentinel) as separator,
    ):
        assert create_separator(MODEL_NAME) is sentinel

    assert separator.call_args.kwargs["target_instrument_override"] == "Vocals"


def test_from_model_name_forwards_catalog_target_override():
    resolved = {
        "model_type": "mel_band_roformer",
        "model_path": "model.ckpt",
        "config_path": "model.yaml",
        "source": "catalog",
        "inference_params": {},
        "target_instrument_override": "Vocals",
    }
    with (
        patch("pymss.model_registry.resolve_model", return_value=resolved),
        patch.object(MSSeparator, "__init__", return_value=None) as initialize,
    ):
        MSSeparator.from_model_name(MODEL_NAME)

    assert initialize.call_args.kwargs["target_instrument_override"] == "Vocals"
