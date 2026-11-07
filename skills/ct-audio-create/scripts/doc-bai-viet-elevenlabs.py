#!/usr/bin/env python3
"""Read a plain .txt article (Vietnamese or English) aloud with the user's own cloned ElevenLabs voice and write an M4A.
Third reader beside doc-bai-viet-vieneu.py and doc-bai-viet-kokoro.py: same text format, same flags, same output
encoding, same parts and timing file. It runs in the cloud (ElevenLabs API, billed per character), so it needs no
model on this machine, only the installer's Python (numpy, soundfile, imageio-ffmpeg).

Keys in .env at the repo root (or the environment): ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (the cloned voice).
  ~/.vieneu-tts/.venv/bin/python <skill>/scripts/doc-bai-viet-elevenlabs.py <audioWork>/<slug>/<slug>.txt
      --sample        (paragraph 2 only, to check the voice first)
      --list-voices   (the account's voices; cloned ones first)
      --dry           (characters to send and the parts that would be read; no call, no cost)
The language comes from the path (`/en/` is English) or --lang. Only sections whose words changed are sent again
(parts.py), so a small edit costs only its own characters; --fresh sends everything.
"""
import argparse, json, os, subprocess, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
from pathlib import Path

import numpy as np
import soundfile as sf

from audio_sync import sync_path, write_sync
from parts import build, find_repo, part_key, sections

API = "https://api.elevenlabs.io/v1"
UA = "content-kit-audio/1.0"
# The highest quality the API gives (pcm_44100, raw 16-bit mono; refused on the lowest plans: --sr 24000), encoded
# HE-AAC 40k mono (user choice 2026-11-07: about 6 MB for 19 minutes) with Apple's encoder: qaac on Windows, the
# ffmpeg of macOS with aac_at. Neither found: AAC-LC 64k (about 9 MB). Parts: Opus 64k, so the joined file is not held
# back by them. The local readers stay at 24 kHz and 56k (their voices are 24 kHz).
SR = 44100
HE_KBPS = 40  # the most Apple's HE-AAC encoder gives one channel
AAC_BITRATE = "64k"
PART_BITRATE = "64k"
PAUSE_SEC = 0.6
# eleven_multilingual_v2 has no Vietnamese; eleven_v3 and the v2.5 models do.
DEFAULT_MODEL = {"vi": "eleven_v4", "en": "eleven_v4"}  # user choice 2026-11-07
# The user's own speaking pace (user choice 2026-11-07): v4 reads Vietnamese too slowly at 1.0, English stays as read.
TEMPO = {"vi": 1.1, "en": 1.0}


def env(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    f = find_repo(Path(__file__).resolve().parent) / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.partition("=")
            if sep and k.strip() == name:
                return v.strip().strip('"').strip("'") or None
    return None


def call(path: str, key: str, body: dict | None = None, tries: int = 5) -> bytes:
    url = API + path
    for n in range(tries):
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"xi-api-key": key, "User-Agent": UA, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:400]
            if e.code in (429, 500, 502, 503, 504) and n < tries - 1:
                time.sleep(2 ** n * 2)
                continue
            raise SystemExit(f"ElevenLabs {e.code}: {msg}")
        except urllib.error.URLError as e:
            if n < tries - 1:
                time.sleep(2 ** n * 2)
                continue
            raise SystemExit(f"ElevenLabs unreachable: {e.reason}")
    raise SystemExit("ElevenLabs: too many retries")


def he_aac_encoder():
    """('qaac', path) on Windows, ('aac_at', ffmpeg) on macOS, or None. qaac: $QAAC, else <VIENEU_HOME>/qaac/*/x64/qaac64.exe
    with Apple's DLLs in QTfiles64 beside it (references/setup.md, "HE-AAC")."""
    import shutil
    if sys.platform == "win32":
        home = Path(os.environ.get("VIENEU_HOME") or Path.home() / ".vieneu-tts")
        found = [Path(os.environ["QAAC"])] if os.environ.get("QAAC") else sorted(home.glob("qaac/*/x64/qaac64.exe"))
        exe = next((p for p in reversed(found) if p.exists()), None) or (shutil.which("qaac64") and Path(shutil.which("qaac64")))
        if exe and subprocess.run([str(exe), "--check"], capture_output=True).returncode == 0:
            return ("qaac", str(exe))
    elif sys.platform == "darwin":
        ff = shutil.which("ffmpeg")
        if ff and "aac_at" in subprocess.run([ff, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout:
            return ("aac_at", ff)
    return None


def main():
    global SR
    ap = argparse.ArgumentParser()
    ap.add_argument("txt", nargs="?")
    ap.add_argument("--voice", help="voice id (default ELEVENLABS_VOICE_ID in .env)")
    ap.add_argument("--model", help="eleven_v4 by default (both languages)")
    ap.add_argument("--lang", choices=["vi", "en"], help="default: en when the path has /en/, else vi")
    ap.add_argument("--stability", type=float, help="0 to 1; default: the voice's own setting")
    ap.add_argument("--similarity", type=float, help="similarity_boost, 0 to 1; default: the voice's own")
    ap.add_argument("--style", type=float, help="0 to 1; default: the voice's own")
    ap.add_argument("--speed", type=float, help="0.7 to 1.2; default: the voice's own")
    ap.add_argument("--tempo", type=float, help="default: vi 1.1, en 1.0. Speed up (or slow down) after the call, pitch kept (ffmpeg atempo, 0.5 to 2); v3 and v4 ignore --speed")
    ap.add_argument("--sr", type=int, choices=[44100, 24000, 22050, 16000], default=SR,
                    help="sample rate asked from ElevenLabs (44100 needs a paid plan)")
    ap.add_argument("--workers", type=int, default=2, help="requests at once (the plan's concurrency limit caps it)")
    ap.add_argument("--format", choices=["m4a", "mp3"], default="m4a")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true", help="read only paragraph 2, as <name>-thu.m4a")
    ap.add_argument("--sync", help="timing file to write (default <paths.audioSync>/<name>.<lang>.json)")
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="read every section again, reusing no part")
    ap.add_argument("--dry", action="store_true", help="count the characters to send; no call")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()
    SR = a.sr

    key = env("ELEVENLABS_API_KEY")
    if not key and not a.dry:
        ap.error("ELEVENLABS_API_KEY is missing: add it to .env at the repo root (key in .env.example)")
    if a.list_voices:
        voices = json.loads(call("/voices", key))["voices"]
        voices.sort(key=lambda v: v.get("category") != "cloned")
        for v in voices:
            print(f"{v['voice_id']}  {v.get('category', ''):<12} {v['name']}")
        return
    if not a.txt:
        ap.error("txt is required")
    voice = a.voice or env("ELEVENLABS_VOICE_ID")
    if not voice:
        ap.error("no voice: set ELEVENLABS_VOICE_ID in .env or pass --voice (ids: --list-voices)")

    src = Path(a.txt)
    lang = a.lang or ("en" if src.resolve().parent.name == "en" else "vi")
    model = a.model or DEFAULT_MODEL[lang]
    if a.tempo is None:
        a.tempo = TEMPO[lang]
    paras = [p.strip() for p in src.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    if a.sample:
        paras = paras[1:2] or paras[:1]

    settings = {k: v for k, v in {"stability": a.stability, "similarity_boost": a.similarity,
                                  "style": a.style, "speed": a.speed}.items() if v is not None}
    engine = {"name": "elevenlabs", "model": model, "voice": voice, "settings": settings, "lang": lang, "sr": SR}
    if a.tempo != 1.0:
        engine["tempo"] = a.tempo  # only when set, so parts read before --tempo existed keep their names
    expressive = model.startswith(("eleven_v3", "eleven_v4"))
    stitch = not expressive  # previous_text / next_text keep the tone between paragraphs; v3 and v4 refuse them
    lang_code = "_v2_5" in model or expressive

    if a.dry:
        todo = paras
        if not a.sample and not a.fresh:
            mf = src.with_name(src.stem + ".parts.json")
            known = {p["key"] for p in json.loads(mf.read_text(encoding="utf-8")).get("parts", [])} if mf.exists() else set()
            todo = [p for _, ps in sections(src, paras) if part_key(engine, PAUSE_SEC, ps) not in known for p in ps]
        print(f"{len(todo)}/{len(paras)} paragraphs to send, {sum(len(p) for p in todo):,} characters, "
              f"model {model}, lang {lang}")
        return
    print(f"{len(paras)} paragraphs, voice {voice}, model {model}, lang {lang}", flush=True)

    def one(i_p):
        i, p, prev, nxt = i_p
        body = {"text": p, "model_id": model}
        if settings:
            body["voice_settings"] = settings
        if lang_code:
            body["language_code"] = lang
        if stitch:
            if prev:
                body["previous_text"] = prev
            if nxt:
                body["next_text"] = nxt
        pcm = call(f"/text-to-speech/{voice}?output_format=pcm_{SR}", key, body)
        if a.tempo != 1.0:
            import imageio_ffmpeg
            pcm = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1",
                                  "-i", "-", "-filter:a", f"atempo={a.tempo}", "-f", "s16le", "-"],
                                 input=pcm, capture_output=True, check=True).stdout
        return np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0

    t0, sent = time.time(), [0]

    def read_many(todo):
        jobs = []
        for i, p in enumerate(todo):
            j = paras.index(p) if p in paras else -1
            prev = paras[j - 1] if j > 0 else ""
            nxt = paras[j + 1] if 0 <= j < len(paras) - 1 else ""
            jobs.append((i, p, prev, nxt))
        with ThreadPoolExecutor(max(1, a.workers)) as ex:
            for n, wav in enumerate(ex.map(one, jobs), 1):
                sent[0] += len(todo[n - 1])
                print(f"{n}/{len(todo)} done ({time.time() - t0:.0f}s)", flush=True)
                yield wav

    if a.sample:
        chunks, lengths = [], []
        for wav in read_many(paras):
            chunks += [wav, np.zeros(int(SR * PAUSE_SEC), dtype=np.float32)]
            lengths.append(len(wav))
        full = np.concatenate(chunks)
    else:
        full, lengths, _ = build(src, lang, paras, engine, SR, PAUSE_SEC, read_many, fresh=a.fresh, part_bitrate=PART_BITRATE)
    print(f"{sent[0]:,} characters sent to ElevenLabs", flush=True)
    suffix = "-thu" if a.sample else ""
    out = Path(a.out) if a.out else src.with_name(src.stem + suffix + "." + a.format)
    if not (a.sample or a.no_sync):
        write_sync(src, lengths, SR, PAUSE_SEC, sync_path(src, lang, a.sync))
    wav = out.with_suffix(".wav")
    sf.write(str(wav), full, SR)

    import imageio_ffmpeg
    he = he_aac_encoder() if a.format == "m4a" else None
    if he and he[0] == "qaac":
        # qaac writes the index first (seekable at once); -s: quiet
        subprocess.run([he[1], "--he", "--cvbr", str(HE_KBPS), "-s", "-o", str(out), str(wav)], check=True)
        kind = f"HE-AAC {HE_KBPS}k (qaac)"
    elif he:
        subprocess.run([he[1], "-y", "-loglevel", "error", "-i", str(wav), "-codec:a", "aac_at", "-profile:a", "aac_he",
                        "-b:a", f"{HE_KBPS}k", "-ac", "1", "-movflags", "+faststart", str(out)], check=True)
        kind = f"HE-AAC {HE_KBPS}k (aac_at)"
    else:
        if a.format == "m4a":
            print("no HE-AAC encoder (qaac on Windows, ffmpeg aac_at on macOS): AAC-LC " + AAC_BITRATE, flush=True)
        # index first (faststart) so the browser can seek
        codec = ["-codec:a", "aac", "-b:a", AAC_BITRATE, "-ac", "1", "-movflags", "+faststart"] if a.format == "m4a" else ["-codec:a", "libmp3lame", "-qscale:a", "4"]
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav), *codec, str(out)], check=True)
        kind = f"AAC-LC {AAC_BITRATE}" if a.format == "m4a" else "MP3"
    wav.unlink()
    print(f"Wrote {out} ({len(full) / SR / 60:.1f} min, {kind})", flush=True)


if __name__ == "__main__":
    main()
