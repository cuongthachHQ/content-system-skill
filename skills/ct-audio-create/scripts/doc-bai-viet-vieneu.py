#!/usr/bin/env python3
"""Read a plain .txt article aloud with VieNeu-TTS v3 Turbo and write an MP3.

Setup once per machine with setup.sh (same folder). Run with the venv it builds:
  ~/.vieneu-tts/.venv/bin/python <skill>/scripts/doc-bai-viet-vieneu.py <audioWork>/<slug>/<slug>.txt
      --voice "Hải Đăng"  --sample   (one short paragraph only, to check the voice first)
      --workers 2   (default; paragraphs read by 2 processes at once, CPU threads split between them; 1 = one after another)
      --list-voices
Blank lines in the text are paragraph breaks. Writes <name>.m4a (AAC, mono, light) next to the .txt, or --out;
--format mp3 for an MP3. With the converter's <name>.src.json beside the .txt it also writes the timing file the player
uses to highlight the block being read: <audioSync>/<name>.vi.json (or --sync; --no-sync skips it).
A full read keeps one audio part per section (an H2, or the lead and each H3 of an H2 with more than 2 H3s) and reads again only the sections whose words changed (parts.py;
--fresh reads everything). A sample never touches the parts.
"""
import argparse, hashlib, os, subprocess, sys, time

# Vietnamese log lines on a Windows console (cp1252) killed the reader with UnicodeEncodeError (2026-11-01): print UTF-8
# whatever the console says (PYTHONUTF8=1 is still a good habit; it also covers the library's own output).
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
from importlib.metadata import version
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from audio_sync import sync_path, write_sync
from parts import build

SR = 48000
PAUSE_SEC = 0.6
MY_VOICE = "Giọng của tôi"

tts = None
voice = None


def load(threads, voice_name, ref):
    """Load the model once per process (threads=0 lets the engine pick)."""
    global tts, voice
    from vieneu import Vieneu
    tts = Vieneu(threads=threads)
    voice = voice_name
    if ref:
        tts.add_voice(MY_VOICE, ref)
        voice = MY_VOICE


def read(p):
    return np.asarray(tts.infer(p, voice=voice), dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("txt", nargs="?")
    ap.add_argument("--voice", default="Hải Đăng")
    ap.add_argument("--format", choices=["m4a", "mp3"], default="m4a")
    ap.add_argument("--ref", help="3-8 s clip of your own voice to clone (overrides --voice)")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true", help="read only paragraph 2, as <name>-thu.m4a")
    # Measured 2026-10-21 on an i5-12400F (6 cores), 12 paragraphs: 1 worker 67 s, 2 workers 50 s, 3 workers 56 s.
    ap.add_argument("--workers", type=int, default=2, help="processes reading paragraphs at once (1 = one after another)")
    ap.add_argument("--sync", help="timing file to write (default <paths.audioSync>/<name>.vi.json)")
    ap.add_argument("--no-sync", action="store_true", help="write no timing file")
    ap.add_argument("--fresh", action="store_true", help="read every section again, reusing no part")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    if a.list_voices:
        load(0, a.voice, None)
        for label, _ in tts.list_preset_voices():
            print(label)
        return
    if not a.txt:
        ap.error("txt is required")

    src = Path(a.txt)
    paras = [p.strip() for p in src.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    if a.sample:
        paras = paras[1:2] or paras[:1]
    # Split the physical cores between the processes (os.cpu_count() counts logical ones, two per core; see read_many).
    workers = max(1, min(a.workers, len(paras)))
    print(f"{len(paras)} paragraphs, voice: {MY_VOICE if a.ref else a.voice}, {workers} worker(s)", flush=True)

    t0 = time.time()

    def read_many(todo):
        """Read the given paragraphs, in order, with the worker processes (started only when something is read)."""
        n = max(1, min(workers, len(todo)))
        th = 0 if n == 1 else max(1, (os.cpu_count() or 2) // 2 // n)
        if n == 1:
            load(th, a.voice, a.ref)
            results, pool = map(read, todo), None
        else:
            pool = Pool(n, initializer=load, initargs=(th, a.voice, a.ref))
            results = pool.imap(read, todo)  # keeps the paragraph order
        for i, wav in enumerate(results, 1):
            print(f"{i}/{len(todo)} done ({time.time() - t0:.0f}s)", flush=True)
            yield wav
        if pool:
            pool.close()
            pool.join()

    if a.sample:
        lengths = []
        chunks = []
        for wav in read_many(paras):
            chunks += [wav, np.zeros(int(SR * PAUSE_SEC), dtype=np.float32)]
            lengths.append(len(wav))
        full = np.concatenate(chunks)
    else:
        # One part per section (an H2, or each H3 of an H2 with more than 2), reused while its words and the voice stay the same (parts.py).
        ref = hashlib.sha1(Path(a.ref).read_bytes()).hexdigest()[:12] if a.ref else None
        engine = {"name": "vieneu", "version": version("vieneu"), "voice": None if a.ref else a.voice, "ref": ref}
        full, lengths, _ = build(src, "vi", paras, engine, SR, PAUSE_SEC, read_many, fresh=a.fresh)
    suffix = "-thu" if a.sample else ""
    out = Path(a.out) if a.out else src.with_name(src.stem + suffix + "." + a.format)
    if not (a.sample or a.no_sync):
        write_sync(src, lengths, SR, PAUSE_SEC, sync_path(src, "vi", a.sync))
    wav = out.with_suffix(".wav")
    import soundfile as sf
    sf.write(str(wav), full, SR)

    import imageio_ffmpeg
    # m4a: AAC 56 kbit/s mono is plenty for a voice (about 7.5 MB for 19 minutes); faststart puts the index first so
    # the browser can seek before the whole file has loaded.
    codec = ["-codec:a", "aac", "-b:a", "56k", "-ac", "1", "-movflags", "+faststart"] if a.format == "m4a" else ["-codec:a", "libmp3lame", "-qscale:a", "4"]
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav), *codec, str(out)], check=True)
    wav.unlink()
    print(f"Wrote {out} ({len(full) / SR / 60:.1f} min)", flush=True)


if __name__ == "__main__":  # required for the worker processes on Windows and macOS
    main()
