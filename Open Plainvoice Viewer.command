#!/bin/zsh
set -eu
cd "${0:A:h}"
PYTHON_BIN="$(command -v python3)"
if "$PYTHON_BIN" -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8876/api/catalog", timeout=1)' >/dev/null 2>&1; then
  open 'http://127.0.0.1:8876/?view=clean'
  exit 0
fi
open 'http://127.0.0.1:8876/?view=clean'
exec "$PYTHON_BIN" scripts/serve_data_viewer.py --database "$PWD/data/local/data-viewer/review.sqlite"
