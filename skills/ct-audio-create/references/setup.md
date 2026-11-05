# Install the two voices (one-time, any machine)

Read it when step 1 of `SKILL.md` finds no working install, or when a command of the readers fails. The installer builds one Python (`PY`, see `SKILL.md`) and never touches the system Python, the repo or the shell profile.

## Run the installer

Tell the user in one line what will be installed, then run the installer for the system (`uname -s` says Darwin or Linux; Windows has no `uname`) in the background with a log file and wait for `READY`:

- macOS or Linux: `bash <skill>/scripts/setup.sh` (`<skill>` is this skill's folder)
- Windows: `powershell -ExecutionPolicy Bypass -File <skill>\scripts\setup.ps1`

About 10 minutes and 1.5 GB: uv from astral.sh (only if missing), Python 3.12, `vieneu`, `imageio-ffmpeg` and `kokoro-onnx` from PyPI, the Vietnamese model from huggingface.co, the Kokoro model (350 MB) from github.com/thewh1teagle/kokoro-onnx releases, everything under `~/.vieneu-tts`, `~/.local/bin` and the Hugging Face cache. The user typing `/content-audio-create` is the approval for exactly this list. The installer needs no sudo, no account and no token, and does not touch the repo, the system Python or the shell profile. Never ask for or print a Hugging Face token. A failed run is safe to repeat.

## Troubleshooting

- Windows, `UnicodeEncodeError: 'charmap' codec can't encode...` when the reader prints a Vietnamese voice name: set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` before running the scripts (PowerShell: `$env:PYTHONUTF8=1`).

- `External data path escapes model directory`: the Hugging Face cache holds symlinks and onnxruntime refuses them. Run the installer again (its last step replaces them with real files).
- The installer says `uv: command not found` right after installing it: it adds `~/.local/bin` (Windows: `%USERPROFILE%\.local\bin`) to its own PATH only. Run it again in the same terminal; it will find uv.
- Import error mentioning `libgomp` or `libsndfile` on a minimal Linux: `sudo apt install libgomp1 libsndfile1` (the user runs this, it needs sudo), then run the installer again.
- The model download stops or is slow: it comes from huggingface.co; run the installer again, it continues. Behind a firewall, set `HF_ENDPOINT` to a mirror the user trusts before running it.
- Not enough disk: the installer stops with a message when less than 4 GB is free; a finished install needs about 1.7 GB.
- Windows: if PowerShell refuses to run the script, use the exact command in step 1 (the bypass is for that one run). A `NativeCommandError` line printed while uv installs is uv's progress on stderr, not a failure: only `READY` or `FAILED` at the end counts.
- System Python is 3.9 or missing: never use it, always `PY` (3.12 from uv).
- A word is read wrong: respell it in `fix.tsv` and rerun step 3.
- Uninstall: delete the `~/.vieneu-tts` folder (both voices; and the Vietnamese model in `~/.cache/huggingface/hub/models--*` if the space matters).
- Colab instead of a local install: `scripts/doc-bai-viet-vieneu.ipynb` (upload the notebook and the `.txt` to colab.research.google.com).
