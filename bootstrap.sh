#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/shreenxdhi/qwen-ane-terminal.git"
QWEN_DIR="${QWEN_ANE_HOME:-$HOME/qwen-ane-terminal}"
export PATH="$HOME/.local/bin:$PATH"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "qwen-ane requires an Apple silicon Mac." >&2
  exit 1
fi

if ! command -v xcrun >/dev/null || ! xcrun --find coremlcompiler >/dev/null 2>&1; then
  echo "macOS needs Xcode Command Line Tools before model conversion." >&2
  xcode-select --install || true
  echo "Finish the macOS installation, then run this installer command again." >&2
  exit 1
fi

if ! command -v git >/dev/null; then
  echo "Git is unavailable. Finish installing Xcode Command Line Tools and retry." >&2
  exit 1
fi

if [[ -d "$QWEN_DIR/.git" ]]; then
  if [[ ! -f "$QWEN_DIR/setup.sh" || ! -f "$QWEN_DIR/run.sh" ]]; then
    echo "Cannot install: $QWEN_DIR is a different Git repository." >&2
    exit 1
  fi
  echo "Using existing checkout: $QWEN_DIR"
elif [[ -e "$QWEN_DIR" ]]; then
  echo "Cannot install: $QWEN_DIR already exists and is not this Git repository." >&2
  exit 1
else
  git clone "$REPO_URL" "$QWEN_DIR"
fi

if [[ ! -f "$QWEN_DIR/models/qwen25-1.5b-ane/meta.yaml" && ! -f "$HOME/Anemll/qwen25-1.5b-ane/meta.yaml" ]]; then
  if ! command -v uv >/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
  fi
  "$QWEN_DIR/setup.sh"
fi

"$QWEN_DIR/install.sh"
echo "Installation complete. Open a new terminal if needed, then run: qwen-ane"
