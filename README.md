# qwen-ane

Run Qwen2.5-1.5B-Instruct in your terminal on Apple silicon. Inference runs locally through [ANEMLL](https://github.com/Anemll/Anemll) and Core ML, with CPU and Neural Engine compute units. The model stays loaded while you chat, and replies stream as they are generated.

## Install

On an Apple silicon Mac with macOS 15 or later:

```sh
curl -fsSL https://raw.githubusercontent.com/shreenxdhi/qwen-ane-terminal/main/bootstrap.sh | bash
```

The installer downloads ANEMLL and the Qwen weights, converts the model, and adds `qwen-ane` to your terminal. Allow about 10 GB of free space. The first conversion takes time; if macOS asks for Xcode Command Line Tools, finish installing them and run the same command again.

Then, from any directory:

```sh
qwen-ane
```

Type a message and press Enter. Use `/exit` or Ctrl+D to leave.

## Usage

```sh
qwen-ane --prompt "Explain how an induction motor works." --max-tokens 96
qwen-ane --plain
```

The first command prints one response and exits. `--plain` shows ANEMLL's full output. In the chat, `/help` lists shortcuts, `/t` toggles thinking mode, and Ctrl+C interrupts generation. Other options accepted by ANEMLL's `chat_full.py`, such as `--st` and `--no-think`, pass through unchanged.

The terminal shows decode speed after each response. Actual speed depends on the Mac, prompt, context, and conversion settings. Core ML chooses how to divide work between the CPU and Neural Engine.

## Existing ANEMLL setup

The installer reuses a conversion at `~/Anemll/qwen25-1.5b-ane` when it finds one. The launcher also works with a model produced inside this repository. If your files are elsewhere, set their paths when launching:

```sh
ANEMLL_DIR=/path/to/Anemll MODEL_META=/path/to/meta.yaml qwen-ane
```

`ANEMLL_DIR` must contain `tests/chat_full.py` and `env-anemll/bin/python`. `MODEL_META` must point to the converted model's `meta.yaml`.

For a manual install, clone this repository, run `./setup.sh`, then run `./install.sh`. The launcher calls ANEMLL's virtual environment directly, so shell aliases for `python` do not affect it.

## Troubleshooting

- **Model not found:** Check that conversion finished and `MODEL_META` points to `meta.yaml`.
- **No `qwen-ane` command:** Open a new terminal after installation. The default command location is `~/.local/bin`.
- **Chat exits or fails to load:** Read `.local/logs/latest.log` in the repository, or run `qwen-ane --plain` for ANEMLL's original output.

The 1.5B conversion path is experimental and may need adjustments as ANEMLL and macOS change.

## Credits

The terminal wrapper is MIT licensed. Conversion and inference use [ANEMLL](https://github.com/Anemll/Anemll); the model is [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct). Their licenses and model terms apply. Neither source weights nor converted models are included in this repository.
