#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${QWEN_ANE_BIN_DIR:-$HOME/.local/bin}"
COMMAND="$BIN_DIR/qwen-ane"

mkdir -p "$BIN_DIR"
if [[ -e "$COMMAND" || -L "$COMMAND" ]]; then
  if [[ -L "$COMMAND" && "$(readlink "$COMMAND")" == "$ROOT/run.sh" ]]; then
    echo "qwen-ane is already installed at $COMMAND"
  else
    echo "Cannot install: $COMMAND already exists. Move it aside or set QWEN_ANE_BIN_DIR." >&2
    exit 1
  fi
else
  ln -s "$ROOT/run.sh" "$COMMAND"
  echo "Installed qwen-ane at $COMMAND"
fi

PATH_ADDED=false
if [[ "$BIN_DIR" == "$HOME/.local/bin" && "${SHELL:-}" == */zsh ]]; then
  ZSHRC="${ZDOTDIR:-$HOME}/.zshrc"
  if [[ ! -f "$ZSHRC" ]] || ! grep -Fq '$HOME/.local/bin' "$ZSHRC"; then
    printf '\n# qwen-ane\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$ZSHRC"
    PATH_ADDED=true
    echo "Added ~/.local/bin to your zsh PATH. Open a new terminal to use qwen-ane."
  fi
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* && "$PATH_ADDED" == false ]]; then
  echo "Add $BIN_DIR to your PATH, then open a new terminal."
  echo "For zsh, add this line to ~/.zshrc: export PATH=\"$BIN_DIR:\$PATH\""
else
  echo "Run it from anywhere: qwen-ane"
fi
