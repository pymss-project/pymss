from __future__ import annotations

import subprocess

import pytest

from pymss import model_download


def test_parse_aria2_progress_line():
    progress = model_download._parse_aria2_progress("[#abcd12 4.0MiB/10MiB(40%) CN:1 DL:512KiB]")

    assert progress == (4 * 1024 * 1024, 10 * 1024 * 1024, "512KiB")


def test_parse_aria2_progress_ignores_unusable_lines():
    assert model_download._parse_aria2_progress("*** Download Progress Summary ***") is None
    # A total of zero means aria2 does not know the size yet, so there is no percentage to report.
    assert model_download._parse_aria2_progress("[#abcd12 4.0MiB/0B(0%) CN:1 DL:512KiB]") is None


def test_urllib_download_emits_byte_progress(monkeypatch, tmp_path):
    class FakeResponse:
        headers = {"content-length": "6"}

        def __init__(self):
            self.chunks = iter([b"abc", b"def", b""])

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return next(self.chunks)

    monkeypatch.setattr(model_download.urllib.request, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    events = []
    dest = tmp_path / "model.pth"

    model_download._download_file_urllib(
        "https://example.test/model.pth",
        tmp_path / "model.pth.part",
        dest,
        timeout=1,
        progress_callback=lambda *args: events.append(args),
    )

    assert dest.read_bytes() == b"abcdef"
    assert events == [
        (0, 6, "Downloading model.pth"),
        (3, 6, "Downloading model.pth"),
        (6, 6, "Downloading model.pth"),
        (6, 6, "Downloaded model.pth"),
    ]


def test_aria2_download_captures_output_and_emits_progress(monkeypatch, tmp_path):
    captured = {}

    class FakeProcess:
        stdout = ["[#abcd12 4.0MiB/10MiB(40%) CN:1 DL:512KiB]\n"]
        returncode = 0

        def __init__(self, cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            output_path = tmp_path / cmd[cmd.index("--out") + 1]
            output_path.write_bytes(b"abcdef")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def wait(self):
            return self.returncode

    monkeypatch.setattr(model_download.subprocess, "Popen", FakeProcess)
    events = []
    dest = tmp_path / "model.pth"

    model_download._download_file_aria2(
        "https://example.test/model.pth",
        tmp_path / "model.pth.part",
        dest,
        expected_size=6,
        timeout=1,
        progress_callback=lambda *args: events.append(args),
    )

    assert dest.read_bytes() == b"abcdef"
    assert captured["kwargs"]["stdout"] == subprocess.PIPE
    assert captured["kwargs"]["stderr"] == subprocess.STDOUT
    assert events == [
        (0, 6, "Downloading model.pth"),
        (4 * 1024 * 1024, 10 * 1024 * 1024, "Downloading model.pth (512KiB/s)"),
        (6, 6, "Downloaded model.pth"),
    ]


def test_a_failing_callback_does_not_retry_the_download(monkeypatch, tmp_path):
    attempts = []

    class FakeResponse:
        headers = {"content-length": "6"}

        def __init__(self):
            self.chunks = iter([b"abc", b"def", b""])

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return next(self.chunks)

    def fake_urlopen(*_args, **_kwargs):
        attempts.append(1)
        return FakeResponse()

    monkeypatch.setattr(model_download.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(model_download, "ARIA2C_PATH", None)

    calls = []

    def faulty_callback(*_args):
        calls.append(1)
        # OSError is what the retry loop watches for, so this is the dangerous shape.
        raise OSError("callback could not write its log")

    dest = tmp_path / "model.pth"
    model_download._download_file(
        "https://example.test/model.pth", dest, timeout=1, progress_callback=faulty_callback
    )

    assert dest.read_bytes() == b"abcdef"
    assert len(attempts) == 1, "a broken callback must not cause the file to be fetched again"
    assert calls, "the callback should still have been attempted"


def test_an_interrupted_read_kills_aria2(monkeypatch, tmp_path):
    killed = []

    class InterruptedProcess:
        def __init__(self, _cmd, **_kwargs):
            self.stdout = self._lines()

        def _lines(self):
            yield "[#abcd12 1.0MiB/10MiB(10%) CN:1 DL:512KiB]\n"
            raise KeyboardInterrupt("simulated Ctrl+C")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def wait(self):
            return 0

        def kill(self):
            killed.append(True)

    monkeypatch.setattr(model_download.subprocess, "Popen", InterruptedProcess)

    with pytest.raises(KeyboardInterrupt):
        model_download._download_file_aria2(
            "https://example.test/model.pth",
            tmp_path / "model.pth.part",
            tmp_path / "model.pth",
            timeout=1,
        )

    # aria2 ignores a closed stdout, so without an explicit kill it outlives the interrupt and
    # keeps writing to the file.
    assert killed, "aria2c must be killed when the read loop is interrupted"


def test_aria2_failure_reports_captured_output(monkeypatch, tmp_path):
    class FailingProcess:
        stdout = ["errorCode=22 The response status is not successful.\n"]

        def __init__(self, _cmd, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def wait(self):
            return 22

    monkeypatch.setattr(model_download.subprocess, "Popen", FailingProcess)

    with pytest.raises(model_download.DownloadError) as excinfo:
        model_download._download_file_aria2(
            "https://example.test/model.pth",
            tmp_path / "model.pth.part",
            tmp_path / "model.pth",
            timeout=1,
        )

    # Capturing aria2's output is only worth it if the diagnosis survives into the exception.
    assert "exit code 22" in str(excinfo.value)
    assert "errorCode=22" in str(excinfo.value)
