import numpy as np
import pytest
import torch
import yaml

from pymss.config import AttrDict
from pymss import get_separation_logger
from pymss.separator import MSSeparator, _model_input_channels, _output_sample_rate
from pymss.user_models import KNOWN_MODEL_TYPES
from pymss_core import detect_model_type, get_model_from_config
from pymss_core.modules.flashsr import FlashSR


FLASHSR_CONFIG = {
    "audio": {"chunk_size": 16000, "num_channels": 1, "sample_rate": 16000, "output_sample_rate": 48000, "min_mean_abs": 0.0},
    "model": {
        "spec_channels": 128, "segment_size": 30, "resblock": "0",
        "resblock_kernel_sizes": [3, 7, 11],
        "resblock_dilation_sizes": [[1, 3, 5], [1, 3, 5], [1, 3, 5]],
        "upsample_rates": [3], "upsample_initial_channel": 32, "upsample_kernel_sizes": [3],
    },
    "training": {"instruments": ["restored"], "target_instrument": "restored"},
    "inference": {"batch_size": 1, "overlap_size": 0},
}


def test_flashsr_is_a_known_model_type():
    assert "flashsr" in KNOWN_MODEL_TYPES


def test_flashsr_is_detected_from_its_model_block():
    assert detect_model_type(FLASHSR_CONFIG) == "flashsr"


def test_flashsr_instantiates_from_config(tmp_path):
    config_path = tmp_path / "flashsr.yaml"
    config_path.write_text(yaml.safe_dump(FLASHSR_CONFIG), encoding="utf-8")
    model, config = get_model_from_config("flashsr", config_path)
    assert isinstance(model, FlashSR)
    assert config.audio.sample_rate == 16000


def test_flashsr_is_mono_and_upsamples_by_three():
    model = FlashSR().eval()
    with torch.inference_mode():
        output = model(torch.zeros(1, 1, 1600))
    assert output.shape == (1, 1, 4800)


def test_flashsr_channel_count_is_one():
    assert _model_input_channels("flashsr", AttrDict(FLASHSR_CONFIG), FlashSR()) == 1


def test_flashsr_output_sample_rate_comes_from_the_config():
    from pymss.separator import _output_sample_rate
    config = AttrDict(FLASHSR_CONFIG)
    assert _output_sample_rate(config) == 48000
    config.audio.output_sample_rate = None
    assert _output_sample_rate(config) == 16000


def test_flashsr_saves_with_the_upsampled_rate(tmp_path, monkeypatch):
    separator = MSSeparator.__new__(MSSeparator)
    separator.model_type = "flashsr"
    separator.model = FlashSR().eval()
    separator.config = AttrDict(FLASHSR_CONFIG)
    separator.logger = get_separation_logger()
    separator.output_format = "wav"
    separator.audio_params = {}
    separator.store_dirs = {"restored": "results"}
    separator.store_dir = str(tmp_path)
    separator.save_as_folder = False
    separator.progress_callback = None
    separator.debug = True
    separator.use_tta = False
    separator.device = "cpu"
    separator.device_ids = []
    separator.output_normalize = False
    separator._stem_batches_to_save = lambda: (("restored",),)
    saved_rates = []
    monkeypatch.setattr(separator, "_submit_save_outputs", lambda executor, results, sr, file_name: saved_rates.append(sr) or [])
    monkeypatch.setattr(separator, "_drain_save_queue", lambda *args, **kwargs: True)

    input_path = tmp_path / "in.wav"
    import soundfile as sf
    sf.write(input_path, np.zeros(32000, dtype=np.float32), 16000)
    separator.process_folder(str(input_path))
    assert saved_rates == [48000]
