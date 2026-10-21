#!/usr/bin/env bash
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  SOURCE_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" == /* ]] || SOURCE="$SOURCE_DIR/$SOURCE"
done
ROOT="$(cd "$(dirname "$SOURCE")" && pwd)"
if [[ -n "${ANEMLL_DIR:-}" ]]; then
  UPSTREAM="$ANEMLL_DIR"
elif [[ -d "$ROOT/.vendor/Anemll" ]]; then
  UPSTREAM="$ROOT/.vendor/Anemll"
else
  UPSTREAM="$HOME/Anemll"
fi

if [[ -z "${MODEL_META:-}" ]]; then
  if [[ -f "$ROOT/models/qwen25-1.5b-ane/meta.yaml" ]]; then
    MODEL_META="$ROOT/models/qwen25-1.5b-ane/meta.yaml"
  else
    MODEL_META="$UPSTREAM/qwen25-1.5b-ane/meta.yaml"
  fi
fi

if [[ ! -f "$MODEL_META" ]]; then
  echo "Converted model not found: $MODEL_META" >&2
  echo "Run ./setup.sh first, or set MODEL_META to your ANEMLL meta.yaml." >&2
  exit 1
fi
if [[ ! -d "$UPSTREAM/env-anemll" ]]; then
  echo "ANEMLL environment not found: $UPSTREAM/env-anemll" >&2
  echo "Run ./setup.sh first, or set ANEMLL_DIR to your ANEMLL checkout." >&2
  exit 1
fi

PYTHON="$UPSTREAM/env-anemll/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "ANEMLL Python interpreter not found: $PYTHON" >&2
  echo "Run ./setup.sh to create the environment." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import coremltools' >/dev/null 2>&1; then
  echo "Core ML Tools is missing from the ANEMLL environment." >&2
  echo "Install it into the interpreter used by this launcher:" >&2
  echo "  $PYTHON -m pip install 'coremltools>=9.0'" >&2
  exit 1
fi

export ANEMLL_DIR="$UPSTREAM"
exec "$PYTHON" "$ROOT/cli.py" --meta "$MODEL_META" "$@"
