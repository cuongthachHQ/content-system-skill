#!/usr/bin/env bash
# One-time setup of the voice readers (VieNeu-TTS v3 Turbo for Vietnamese, Kokoro-82M for English) on macOS or Linux
# (x86_64 or arm64).
# Windows: use setup.ps1 in this folder. Safe to run again: every finished step is skipped.
#
# Where things go (nothing goes into the repo, the system Python or your shell profile; no account, token or sudo):
#   $VIENEU_HOME (default ~/.vieneu-tts)  the Python 3.12 environment
#   ~/.local/bin                          uv, the installer and Python manager (only when it is missing)
#   $HF_HOME (default ~/.cache/huggingface)  the Vietnamese voice model, about 540 MB
#   $VIENEU_HOME/kokoro                   the English voice model (Kokoro v1.0 from GitHub), about 350 MB
# Total download about 1.5 GB, about 10 minutes. Delete the first folder to uninstall.
set -euo pipefail

HOME_DIR="${VIENEU_HOME:-$HOME/.vieneu-tts}"
PY="$HOME_DIR/.venv/bin/python"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "[0/6] checking this machine ($OS $ARCH)"
case "$OS" in
  Darwin|Linux) ;;
  *) echo "Unsupported system: $OS. On Windows run setup.ps1, or use the Colab notebook."; exit 1 ;;
esac
case "$ARCH" in
  arm64|aarch64|x86_64|amd64) ;;
  *) echo "Unsupported CPU: $ARCH (a 64-bit CPU is needed)."; exit 1 ;;
esac
if [ ! -x "$PY" ]; then
  FREE_MB=$(( $(df -Pk "$HOME" | awk 'NR==2{print $4}') / 1024 ))
  [ "$FREE_MB" -gt 4000 ] || { echo "Need about 4 GB free in $HOME (found $FREE_MB MB)."; exit 1; }
fi

echo "[1/6] uv"
if ! command -v uv >/dev/null 2>&1; then
  # UV_NO_MODIFY_PATH keeps the installer from editing .zshrc or .bashrc
  if command -v curl >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
  elif command -v wget >/dev/null 2>&1; then wget -qO- https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
  else echo "Need curl or wget to download uv (macOS has curl; on Debian or Ubuntu: sudo apt install curl)."; exit 1
  fi
fi

echo "[2/6] Python 3.12 environment"
[ -x "$PY" ] || uv venv --python 3.12 "$HOME_DIR/.venv"

echo "[3/6] vieneu 3.8.3 and ffmpeg (the version Sano pins)"
"$PY" -c "import vieneu, imageio_ffmpeg" 2>/dev/null || uv pip install --python "$PY" "vieneu==3.8.3" imageio-ffmpeg

echo "[4/6] model download (about 540 MB, first time only; retries if the network drops)"
for try in 1 2 3; do
  "$PY" -c "from vieneu import Vieneu; Vieneu()" >/dev/null 2>&1 && break
  echo "  load attempt $try did not finish (the first one is expected to fail on the symlink cache, see the next step)"
  sleep 3
done

echo "[5/6] turn the cache's symlinks into real files (onnxruntime refuses symlinked model files)"
"$PY" - <<'PY'
import glob, os, shutil
hf = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
n = 0
for snap in glob.glob(os.path.join(hf, "hub", "models--*", "snapshots", "*")):
    for root, _, files in os.walk(snap):
        for f in files:
            p = os.path.join(root, f)
            if os.path.islink(p):
                t = os.path.realpath(p); os.remove(p); shutil.copy2(t, p); n += 1
print("symlinks replaced:", n)
PY

echo "[6/6] English voice: kokoro-onnx 0.6.1 and the Kokoro v1.0 model (about 350 MB, first time only)"
"$PY" -c "import kokoro_onnx" 2>/dev/null || uv pip install --python "$PY" "kokoro-onnx==0.6.1"
mkdir -p "$HOME_DIR/kokoro"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "$HOME_DIR/kokoro/$f" ]; then
    curl -fL --retry 3 -o "$HOME_DIR/kokoro/$f.part" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
    mv "$HOME_DIR/kokoro/$f.part" "$HOME_DIR/kokoro/$f"
  fi
done

if "$PY" -c "from vieneu import Vieneu; Vieneu()" && "$PY" -c "import kokoro_onnx" && [ -s "$HOME_DIR/kokoro/voices-v1.0.bin" ]; then
  echo "READY: voice readers work (Vietnamese and English). Python: $PY"
else
  echo "FAILED: the voice reader did not load."
  [ "$OS" = "Linux" ] && echo "On a minimal Debian or Ubuntu try: sudo apt install libgomp1 libsndfile1  (then run this script again)."
  echo "If the model download keeps failing, check the network (Vietnamese from huggingface.co, English from github.com) and run this script again."
  exit 1
fi
