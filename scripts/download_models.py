"""Download the two official Qwen3-TTS snapshots into local model folders."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import snapshot_download


MODELS = {
    "generation": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "clone": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-root", default=os.getenv("QWEN_TTS_MODEL_ROOT", "models"))
    parser.add_argument("--force", action="store_true", help="Re-run download even when model.safetensors exists")
    args = parser.parse_args()
    root = Path(args.model_root).expanduser()
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[1] / root

    for key, model_id in MODELS.items():
        target = root / ("voice_design_1.7b" if key == "generation" else "voice_clone_1.7b")
        marker = target / "model.safetensors"
        if marker.exists() and not args.force:
            print(f"[{key}] already present: {target}")
            continue
        target.mkdir(parents=True, exist_ok=True)
        print(f"[{key}] downloading {model_id} -> {target}")
        snapshot_download(repo_id=model_id, local_dir=str(target), token=os.getenv("HF_TOKEN"))
        if not marker.exists():
            raise RuntimeError(f"Download completed but expected marker is missing: {marker}")
        print(f"[{key}] ready")


if __name__ == "__main__":
    main()
