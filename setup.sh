#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPSTREAM="$ROOT/.vendor/Anemll"
MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-1.5B-Instruct}"
MODEL_OUT="${MODEL_OUT:-$ROOT/models/qwen25-1.5b-ane}"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This setup requires an Apple silicon Mac running macOS." >&2
  exit 1
fi
if ! command -v xcrun >/dev/null || ! xcrun --find coremlcompiler >/dev/null 2>&1; then
  echo "Install Xcode Command Line Tools first: xcode-select --install" >&2
  exit 1
fi
if ! command -v uv >/dev/null; then
  echo "Install uv first: brew install uv" >&2
  exit 1
fi

if [[ ! -d "$UPSTREAM/.git" ]]; then
  mkdir -p "$ROOT/.vendor"
  git clone https://github.com/Anemll/Anemll.git "$UPSTREAM"
fi

cd "$UPSTREAM"
if [[ ! -d env-anemll ]]; then
  ./create_uv_env.sh
fi
./install_dependencies.sh

PYTHON="$UPSTREAM/env-anemll/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "ANEMLL environment was not created at $PYTHON" >&2
  exit 1
fi
if ! "$PYTHON" -c 'import coremltools' >/dev/null 2>&1; then
  echo "Core ML Tools installation did not complete in $PYTHON" >&2
  echo "Try: $PYTHON -m pip install 'coremltools>=9.0'" >&2
  exit 1
fi

mkdir -p "$MODEL_OUT"
./anemll/utils/convert_model.sh --model "$MODEL_ID" --output "$MODEL_OUT"

if [[ ! -f "$MODEL_OUT/meta.yaml" ]]; then
  echo "Conversion returned without producing $MODEL_OUT/meta.yaml." >&2
  echo "Check the ANEMLL conversion output; Qwen 2.5 1.5B is experimental." >&2
  exit 1
fi

printf '\nConversion complete. Run %s/install.sh, then launch with qwen-ane.\n' "$ROOT"
