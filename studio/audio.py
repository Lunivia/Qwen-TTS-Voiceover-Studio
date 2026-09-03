from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
import soundfile as sf


WINDOWS_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def ffmpeg_executable() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def safe_filename(value: str, fallback: str = "audio") -> str:
    cleaned = WINDOWS_INVALID.sub("_", value).strip(" ._")
    return (cleaned or fallback)[:80]


def run_ffmpeg(arguments: list[str]) -> None:
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    completed = subprocess.run(
        [ffmpeg_executable(), "-hide_banner", "-loglevel", "error", "-y", *arguments],
        capture_output=True,
        text=True,
        creationflags=flags,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg conversion failed")


def normalize_to_wav(source: str | Path, destination: str | Path) -> Path:
    source_path = Path(source)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([
        "-i", str(source_path),
        "-vn", "-ac", "1", "-ar", "24000",
        "-c:a", "pcm_s16le", str(destination_path),
    ])
    return destination_path


def wav_to_mp3(source: str | Path, destination: str | Path, bitrate: str = "128k") -> Path:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([
        "-i", str(source),
        "-vn", "-ac", "1", "-ar", "24000",
        "-c:a", "libmp3lame", "-b:a", bitrate,
        str(destination_path),
    ])
    return destination_path


def write_wav(destination: str | Path, waveform, sample_rate: int) -> Path:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(destination_path, waveform, sample_rate, subtype="PCM_16")
    return destination_path


def copy_original(source: str | Path, destination_dir: str | Path) -> Path:
    source_path = Path(source)
    target = Path(destination_dir) / f"original{source_path.suffix.lower()}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target)
    return target


def audio_summary(path: str | Path) -> str:
    info = sf.info(path)
    return f"{info.duration:.2f}s · {info.samplerate}Hz · {info.channels}ch"

