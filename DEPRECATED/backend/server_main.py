"""PyInstaller entry point for Lemma backend server."""
import sys
import os

# 确保 bundled domains 目录在路径中
_bundle_dir = os.path.dirname(os.path.abspath(__file__))

import uvicorn
from lemma.api.server import app


def main():
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8766,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
