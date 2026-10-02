"""Exercise model loading, chunking, output reconstruction and release on DirectML."""

import numpy as np
import pytest
import torch
import yaml
from pymss_core import get_model_from_config

from pymss import MSSeparator


@pytest.mark.integration
@pytest.mark.parametrize("outer_inference", [False, True])
def test_directml_separator_matches_cpu_and_releases_model(tmp_path, outer_inference):
    dml = pytest.importorskip("torch_directml")
    if not dml.is_available():
        pytest.skip("DirectML requires a usable DX12 adapter")
    config = {
        "audio": {"chunk_size": 128, "sample_rate": 44100, "num_channels": 2},
        "model": {
            "dim": 8, "depth": 1, "heads": 2, "dim_head": 4,
            "stereo": True, "num_stems": 1,
            "time_transformer_depth": 1, "freq_transformer_depth": 1,
            "freqs_per_bands": [4, 5], "stft_n_fft": 16,
            "stft_hop_length": 4, "stft_win_length": 16, "mask_estimator_depth": 1,
        },
        "training": {"instruments": ["vocals", "other"], "target_instrument": "vocals", "use_amp": True},
        "inference": {"batch_size": 2, "overlap_size": 16},
    }
    config_path = tmp_path / "model.yaml"
    checkpoint = tmp_path / "model.ckpt"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    torch.manual_seed(17)
    model, _ = get_model_from_config("bs_roformer", config_path)
    torch.save(model.half().state_dict(), checkpoint)
    wave = np.sin(np.arange(293, dtype=np.float32) * 0.1) * 0.1
    audio = np.stack((wave, -wave * 0.4))
    original = audio.copy()
    results = {}
    for device in ("cpu", "dml"):
        with MSSeparator(
            model_type="bs_roformer", model_path=checkpoint, config_path=config_path,
            device=device, device_ids=[0], debug=False,
        ) as separator:
            if device == "dml":
                assert next(separator.model.parameters()).device.type == "privateuseone"
                assert next(separator.model.parameters()).dtype == torch.float32
                seen = []
                handle = separator.model.register_forward_pre_hook(
                    lambda module, args: seen.append((args[0].device.type, torch.is_grad_enabled(),
                                                     torch.is_inference_mode_enabled(), args[0].is_inference()))
                )
            with torch.inference_mode(outer_inference):
                results[device] = separator.separate(audio, pbar=False)
                assert torch.is_inference_mode_enabled() is outer_inference
            if device == "dml":
                handle.remove()
                assert seen and set(seen) == {("privateuseone", False, False, False)}
        assert separator.model is None
        assert separator.config is None
    for stem in ("vocals", "other"):
        assert results["dml"][stem].shape == audio.T.shape
        assert np.isfinite(results["dml"][stem]).all()
        np.testing.assert_allclose(results["dml"][stem], results["cpu"][stem], atol=2e-5, rtol=2e-4)
    np.testing.assert_allclose(results["dml"]["vocals"] + results["dml"]["other"], audio.T, atol=1e-6)
    np.testing.assert_array_equal(audio, original)


@pytest.mark.integration
def test_directml_vr_keeps_spectral_reconstruction_on_cpu():
    dml = pytest.importorskip("torch_directml")
    if not dml.is_available():
        pytest.skip("DirectML requires a usable DX12 adapter")
    from pymss.modules.vocal_remover.vr_separator import VRSeparator
    from pymss_core.modules.vocal_remover import CascadedNet

    torch.manual_seed(23)
    model = CascadedNet(n_fft=256, nn_arch_size=56817, nout=4, nout_lstm=16).eval()
    rng = np.random.default_rng(7)
    spectrum = (rng.standard_normal((2, 129, 96)) + 1j * rng.standard_normal((2, 129, 96))).astype(np.complex64)
    aggression = {"value": 0.05, "split_bin": 32, "aggr_correction": None}
    results = []
    for device in (torch.device("cpu"), dml.device(0)):
        separator = VRSeparator.__new__(VRSeparator)
        separator.model_run = model.to(device)
        separator.torch_device = device
        separator.mps_model_backend = "torch"
        separator.window_size = 512
        separator.batch_size = 1
        separator.debug = False
        separator.progress_callback = None
        separator.use_channels_last = False
        separator.use_amp = True
        separator.enable_tta = True
        separator.enable_post_process = False
        separator.primary_stem_name = "Vocals"
        result = separator.inference_vr(spectrum, device, aggression)
        assert all(np.isfinite(item).all() for item in result)
        np.testing.assert_allclose(sum(result), spectrum, atol=1e-6)
        results.append(result)
    for gpu, cpu in zip(results[1], results[0]):
        np.testing.assert_allclose(gpu, cpu, atol=2e-5, rtol=2e-4)
