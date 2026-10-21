#!/usr/bin/env python3
"""A quiet, streaming terminal interface for ANEMLL's full chat runner.

ANEMLL owns model loading, KV state, generation, and conversation history. This
module only handles terminal presentation and keeps diagnostic output in a log.
"""

from __future__ import annotations

import argparse
import builtins
import contextlib
import importlib.util
import os
import re
import shutil
import sys
import traceback
from pathlib import Path
from threading import Lock
from typing import Optional


ANSI = re.compile(r"\x1b\[[0-9;]*m")
STATS = re.compile(
    r"(?P<speed>[\d.]+) t/s, TTFT: (?P<first>[\d.]+)ms .*?, (?P<tokens>\d+) tokens"
)
OUT = sys.__stdout__
ERR = sys.__stderr__


class Terminal:
    def __init__(self, meta: Path, prompt: Optional[str], log_path: Path) -> None:
        self.meta = meta
        self.prompt = prompt
        self.log_path = log_path
        self.color = OUT.isatty() and "NO_COLOR" not in os.environ
        self.ready = False
        self.answer_started = False
        self.line_start = True
        self.lock = Lock()

    def style(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def write(self, text: str) -> None:
        with self.lock:
            OUT.write(text)
            OUT.flush()

    def panel_line(self, text: str, width: int) -> str:
        available = width - 4
        if len(text) > available:
            text = text[: available - 1] + "…"
        return "│  " + text.ljust(available) + "│"

    def header(self) -> None:
        width = max(42, min(shutil.get_terminal_size((80, 24)).columns, 86))
        rule = "─" * (width - 2)
        lines = [
            "╭" + rule + "╮",
            self.panel_line("◈  QWEN / ANE", width),
            self.panel_line("Private chat on Apple silicon", width),
            "├" + rule + "┤",
            self.panel_line("Model     Qwen 2.5 1.5B Instruct", width),
            self.panel_line("Runtime   Core ML · CPU + Neural Engine", width),
            self.panel_line(f"Model file   {self.meta.parent}", width),
            "╰" + rule + "╯",
        ]
        self.write(self.style("\n".join(lines), "38;5;81") + "\n")
        if self.prompt is None:
            self.write(self.style("  /help commands   /t thinking   Ctrl+D exit\n\n", "38;5;245"))
        else:
            self.write("\n")
        self.write(self.style("  ◌ Loading Core ML model…\n", "38;5;245"))

    def mark_ready(self) -> None:
        if not self.ready:
            self.ready = True
            self.write(self.style("  ● Ready\n", "38;5;120"))

    def show_prompt(self, value: str) -> None:
        lines = value.splitlines() or [""]
        self.write("\n" + self.style("  ❯ ", "38;5;81") + lines[0] + "\n")
        for line in lines[1:]:
            self.write("    " + line + "\n")

    def input(self) -> str:
        self.mark_ready()
        while True:
            self.write("\n" + self.style("  ❯ ", "38;5;81"))
            value = builtins.input().strip()
            if value == "/help":
                self.write(
                    self.style(
                        "\n  Enter a message to chat. /t toggles thinking. "
                        "/exit leaves the session. Ctrl+C interrupts generation.\n",
                        "38;5;245",
                    )
                )
                continue
            if value in {"/exit", "/quit"}:
                raise EOFError
            return value

    def start_answer(self) -> None:
        if self.answer_started:
            return
        self.mark_ready()
        if self.prompt is not None:
            self.show_prompt(self.prompt)
        self.write("\n" + self.style("  ✦ Qwen\n", "38;5;120"))
        self.answer_started = True
        self.line_start = True

    def stream_token(self, value: str) -> None:
        clean = ANSI.sub("", value).replace("\r", "")
        if not clean:
            return
        self.start_answer()
        for part in clean.splitlines(keepends=True):
            if self.line_start:
                self.write(self.style("  │ ", "38;5;81"))
                self.line_start = False
            self.write(part)
            if part.endswith("\n"):
                self.line_start = True

    def finish_answer(self) -> None:
        if self.answer_started:
            if not self.line_start:
                self.write("\n")
            self.answer_started = False
            self.line_start = True

    def print(self, *args: object, **kwargs: object) -> None:
        """Replace ANEMLL's module-level print without changing inference code."""
        # stdout is redirected to the local diagnostic log while ANEMLL runs.
        builtins.print(*args, **kwargs)
        separator = str(kwargs.get("sep", " "))
        value = separator.join(str(arg) for arg in args)
        clean = ANSI.sub("", value).strip()
        end = kwargs.get("end", "\n")

        if end == "" and clean:
            self.stream_token(value)
            return
        if "Assistant:" in clean and end == " ":
            self.start_answer()
            return
        if clean == "" and self.answer_started:
            self.finish_answer()
            return
        match = STATS.search(clean)
        if match:
            self.finish_answer()
            self.write(
                self.style(
                    f"  {match['speed']} tok/s decode  ·  "
                    f"{match['first']} ms first token  ·  {match['tokens']} tokens\n",
                    "38;5;245",
                )
            )
            return
        if clean.startswith("[SYSTEM]"):
            self.write(self.style("  Note: " + clean.removeprefix("[SYSTEM]").strip() + "\n", "38;5;245"))
        elif clean.startswith("Thinking mode"):
            if self.ready:
                self.write(self.style("  " + clean + "\n", "38;5;245"))
        elif clean.startswith("Generation interrupted"):
            self.finish_answer()
            self.write(self.style("  Generation interrupted\n", "38;5;214"))
        elif clean.startswith("Error"):
            self.finish_answer()
            self.write(self.style("  " + clean + "\n", "38;5;203"))
        elif clean.startswith("Exiting chat"):
            self.write(self.style("\n  Session closed.\n", "38;5;245"))


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="A local Qwen chat terminal powered by ANEMLL and Apple Core ML.",
        epilog="Other options are passed to ANEMLL's chat_full.py (for example --st or --no-think).",
    )
    parser.add_argument("--meta", type=Path, help="Path to the converted model's meta.yaml")
    parser.add_argument("--prompt", help="Generate one response and exit")
    parser.add_argument("--plain", action="store_true", help="Show ANEMLL's unfiltered output")
    return parser.parse_known_args()


def main() -> int:
    args, remaining = parse_args()
    root = Path(__file__).resolve().parent
    upstream = Path(os.environ.get("ANEMLL_DIR", root / ".vendor" / "Anemll")).expanduser().resolve()
    runner = upstream / "tests" / "chat_full.py"
    meta = (args.meta or Path(os.environ.get("MODEL_META", root / "models/qwen25-1.5b-ane/meta.yaml"))).expanduser().resolve()

    if not runner.is_file():
        print(f"ANEMLL full chat runner not found: {runner}", file=ERR)
        print("Run ./setup.sh or set ANEMLL_DIR to an ANEMLL checkout.", file=ERR)
        return 1
    if not meta.is_file():
        print(f"Converted model metadata not found: {meta}", file=ERR)
        print("Run ./setup.sh or set MODEL_META to a completed meta.yaml.", file=ERR)
        return 1

    runner_args = ["--meta", str(meta), *remaining]
    if args.prompt is not None:
        runner_args += ["--prompt", args.prompt]
    if args.plain:
        os.execv(sys.executable, [sys.executable, str(runner), *runner_args])

    log_path = root / ".local" / "logs" / "latest.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ui = Terminal(meta, args.prompt, log_path)
    ui.header()

    original_argv = sys.argv
    try:
        with log_path.open("w", encoding="utf-8", buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                spec = importlib.util.spec_from_file_location("anemll_full_chat", runner)
                if spec is None or spec.loader is None:
                    raise RuntimeError(f"Could not load {runner}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.print = ui.print
                module.input = ui.input
                sys.argv = [str(runner), *runner_args]
                result = module.main()
    except (KeyboardInterrupt, EOFError):
        ui.finish_answer()
        ui.write(ui.style("\n  Session closed.\n", "38;5;245"))
        return 0
    except Exception:
        with log_path.open("a", encoding="utf-8") as log:
            traceback.print_exc(file=log)
        ui.finish_answer()
        ui.write(ui.style(f"\n  Could not run the model. Details: {log_path}\n", "38;5;203"))
        return 1
    finally:
        sys.argv = original_argv

    if result not in (0, None):
        ui.write(ui.style(f"\n  ANEMLL exited with code {result}. Details: {log_path}\n", "38;5;203"))
        return int(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
