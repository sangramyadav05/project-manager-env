from __future__ import annotations

import importlib.util
from pathlib import Path

import uvicorn


ROOT_SERVER_PATH = Path(__file__).resolve().parents[1] / "server.py"


def load_app():
    spec = importlib.util.spec_from_file_location("root_server_module", ROOT_SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load root server module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


app = load_app()


def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
