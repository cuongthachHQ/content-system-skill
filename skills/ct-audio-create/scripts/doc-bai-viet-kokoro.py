#!/usr/bin/env python3
"""Read a plain English .txt article aloud with Kokoro-82M (kokoro-onnx) and write an M4A. English twin of
doc-bai-viet-vieneu.py: same text format, same flags, same output encoding.

Setup once per machine with setup.sh or setup.ps1 (same folder): it installs kokoro-onnx into the VieNeu environment and
puts the model in ~/.vieneu-tts/kokoro (or $VIENEU_HOME/kokoro). Run with that environment's Python:
  ~/.vieneu-tts/.venv/bin/python <skill>/scripts/doc-bai-viet-kokoro.py <audioWork>/<slug>/en/<slug>.txt
      --voice am_michael  --sample   (one short paragraph only, to check the voice first)
      --list-voices
Blank lines in the text are paragraph breaks. Writes <name>.m4a (AAC, mono, light) next to the .txt, or --out;
--format mp3 for an MP3. Voices starting with "a" are American English, "b" British English. With the converter's
<name>.src.json beside the .txt it also writes the player's timing file <audioSync>/<name>.en.json
(or --sync; --no-sync skips it). A full read keeps one audio part per H2 section and reads again only the sections
whose words changed (parts.py; --fresh reads everything). A sample never touches the parts.
"""
import argparse, os, subprocess, sys, time

# Vietnamese file names and headings on a Windows console (cp1252): print UTF-8 whatever the console says.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
from importlib.metadata import version
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

from audio_sync import sync_path, write_sync
from parts import build

PAUSE_SEC = 0.6
MODEL_DIR = Path(os.environ.get("VIENEU_HOME") or Path.home() / ".vieneu-tts") / "kokoro"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("txt", nargs="?")
    ap.add_argument("--voice", default="am_michael", help="the site's English voice (user choice 2026-10-21)")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--format", choices=["m4a", "mp3"], default="m4a")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true", help="read only paragraph 2, as <name>-thu.m4a")
    ap.add_argument("--sync", help="timing file to write (default <paths.audioSync>/<name>.en.json)")
    ap.add_argument("--no-sync", action="store_true", help="write no timing file")
    ap.add_argument("--fresh", action="store_true", help="read every section again, reusing no part")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    model, voices = MODEL_DIR / "kokoro-v1.0.onnx", MODEL_DIR / "voices-v1.0.bin"
    if not (model.exists() and voices.exists()):
        ap.error(f"Kokoro model not found in {MODEL_DIR}: run setup.sh or setup.ps1 (same folder) first")
    k = Kokoro(str(model), str(voices))
    if a.list_voices:
        print("\n".join(k.get_voices()))
        return
    if not a.txt:
        ap.error("txt is required")

    src = Path(a.txt)
    paras = [p.strip() for p in src.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    if a.sample:
        paras = paras[1:2] or paras[:1]
    lang = "en-gb" if a.voice.startswith("b") else "en-us"
    print(f"{len(paras)} paragraphs, voice: {a.voice} ({lang})", flush=True)

    sr, t0 = 24000, time.time()  # Kokoro v1.0 always speaks at 24 kHz

    def read_many(todo):
        for i, p in enumerate(todo, 1):
            wav, rate = k.create(p, voice=a.voice, speed=a.speed, lang=lang)
            if rate != sr:
                raise SystemExit(f"Kokoro returned {rate} Hz, expected {sr}")
            print(f"{i}/{len(todo)} done ({time.time() - t0:.0f}s)", flush=True)
            yield np.asarray(wav, dtype=np.float32)

    if a.sample:
        chunks, lengths = [], []
        for wav in read_many(paras):
            chunks += [wav, np.zeros(int(sr * PAUSE_SEC), dtype=np.float32)]
            lengths.append(len(wav))
        full = np.concatenate(chunks)
    else:
        # One part per H2 section, reused while its words and the voice stay the same (parts.py).
        engine = {"name": "kokoro", "version": version("kokoro-onnx"), "model": "v1.0", "voice": a.voice,
                  "speed": a.speed, "lang": lang}
        full, lengths, _ = build(src, "en", paras, engine, sr, PAUSE_SEC, read_many, fresh=a.fresh)
    suffix = "-thu" if a.sample else ""
    out = Path(a.out) if a.out else src.with_name(src.stem + suffix + "." + a.format)
    if not (a.sample or a.no_sync):
        write_sync(src, lengths, sr, PAUSE_SEC, sync_path(src, "en", a.sync))
    wav = out.with_suffix(".wav")
    sf.write(str(wav), full, sr)

    import imageio_ffmpeg
    # Same encoding as the Vietnamese audio: AAC 56 kbit/s mono with the index first (faststart) so the browser can seek.
    codec = ["-codec:a", "aac", "-b:a", "56k", "-ac", "1", "-movflags", "+faststart"] if a.format == "m4a" else ["-codec:a", "libmp3lame", "-qscale:a", "4"]
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav), *codec, str(out)], check=True)
    wav.unlink()
    print(f"Wrote {out} ({len(full) / sr / 60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()
