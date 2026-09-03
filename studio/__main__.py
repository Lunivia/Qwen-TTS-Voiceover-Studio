from __future__ import annotations

import argparse

from .config import PROJECT_DIR
from .ui import STUDIO_CSS, STUDIO_THEME, build_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Qwen3 TTS local voice studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7870)
    args = parser.parse_args()
    app = build_app()
    app.queue(default_concurrency_limit=1).launch(
        server_name=args.host,
        server_port=args.port,
        share=False,
        show_error=True,
        allowed_paths=[str(PROJECT_DIR)],
        theme=STUDIO_THEME,
        css=STUDIO_CSS,
    )


if __name__ == "__main__":
    main()
