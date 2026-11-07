"""Audio parts, one per section (the opening, each H2, or the lead and each H3 of an H2 with more than 2 H3s; 2026-11-06), shared by both readers (doc-bai-viet-vieneu.py, doc-bai-viet-kokoro.py): a reader
reads again only the sections whose words (or voice) changed and joins every part into the one file the site plays.

- A part's name is a hash of what makes its sound: engine, voice settings, pause and the section's spoken text. Same
  words, same voice -> same name; any change -> a new name, so a name is never reused for another sound.
- Parts are Opus 48 kbit/s mono, lighter than the joined M4A (user choice 2026-11-05: parts only serve to build it,
  so R2 holds about 1.9x the joined file, not 2.7x as at 96k). Each part always comes from the original read, so the
  joined file is one transcode away from the voice however often the post is edited.
- Where they live: R2, `parts/<slug>.<lang>/<hash>.opus` under the public audio address (`audio.base` in
  content.config.json), uploaded by publish.mjs; while a run needs them, in `<txt folder>/parts/` (git-ignored, emptied
  by publish.mjs). A part missing on this machine is fetched from R2 over HTTPS (no key needed).
- The repo tracks only `<slug>.parts.json` beside the .txt: the parts in reading order with the samples of each
  paragraph (the timing file needs them) and which parts are on R2 (`published`).
The sections come from the converter's `<slug>.sections.json` (md-to-tts-txt.py); without it the whole text is one part.
"""
import hashlib, json, subprocess, urllib.error, urllib.request
from pathlib import Path

import numpy as np

PART_BITRATE = "48k"
UA = "content-kit-audio/1.0"


def find_repo(start: Path) -> Path:
    """Nearest folder above holding content.config.json (the same rule as content/lib/config.mjs)."""
    for d in [start, *start.parents]:
        if (d / "content.config.json").exists():
            return d
    raise SystemExit(f"no content.config.json above {start}")


def audio_cfg() -> dict:
    repo = find_repo(Path(__file__).resolve().parent)
    cfg = json.loads((repo / "content.config.json").read_text(encoding="utf-8"))
    return {"repo": repo, **(cfg.get("audio") or {})}


def audio_base() -> str:
    base = audio_cfg().get("base")
    if not base:
        raise SystemExit("content.config.json has no audio.base (the public address of the audio)")
    return base.rstrip("/")


def repo_store() -> Path | None:
    """The site's public audio folder when the audio is kept in the repo (audio.dir), else None (R2)."""
    a = audio_cfg()
    return (a["repo"] / a["dir"]) if a.get("dir") else None


def ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def encode_opus(audio: np.ndarray, sr: int, out: Path, bitrate: str = PART_BITRATE) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
           "-c:a", "libopus", "-b:a", bitrate, "-application", "audio", "-f", "ogg", str(out)]  # -f: out may be .opus.tmp
    subprocess.run(cmd, input=np.ascontiguousarray(audio, dtype=np.float32).tobytes(), check=True)


def decode(path: Path, sr: int, samples: int) -> np.ndarray:
    """Decode to mono float32 at sr, trimmed or padded to exactly `samples` (Opus can differ by a few samples)."""
    cmd = [ffmpeg(), "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"]
    a = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)
    return a[:samples] if len(a) >= samples else np.concatenate([a, np.zeros(samples - len(a), dtype=np.float32)])


def sections(txt: Path, paras: list[str]) -> list[tuple[str, list[str]]]:
    f = txt.with_name(txt.stem + ".sections.json")
    if f.exists():
        secs = json.loads(f.read_text(encoding="utf-8"))
        if sum(s["n"] for s in secs) == len(paras):
            out, i = [], 0
            for s in secs:
                out.append((s["h"], paras[i:i + s["n"]]))
                i += s["n"]
            return out
        print(f"{f.name} counts {sum(s['n'] for s in secs)} paragraphs, the .txt has {len(paras)}: one part (rerun md-to-tts-txt.py)", flush=True)
    else:
        print(f"no {f.name}: the whole text is one part (rerun md-to-tts-txt.py to get one part per section)", flush=True)
    return [("", paras)]


def part_key(engine: dict, pause_sec: float, paras: list[str]) -> str:
    blob = json.dumps({"engine": engine, "pause": pause_sec, "paras": paras}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def groups(ps: list[str], group_min: int) -> list[list[str]]:
    """Consecutive paragraphs of one section, gathered until a group holds group_min characters (user decision
    2026-11-07, the ElevenLabs reader: an edit sends one group, not the whole section). A short heading or line joins the
    paragraph after it; a short tail joins the group before it. group_min 0: the section is one group."""
    if group_min <= 0:
        return [ps]
    out, cur, n = [], [], 0
    for p in ps:
        cur.append(p)
        n += len(p)
        if n >= group_min:
            out.append(cur)
            cur, n = [], 0
    if cur:
        if out:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def plan_parts(txt: Path, paras: list[str], engine: dict, pause_sec: float, known: dict, group_min: int = 0):
    """[(heading, paragraphs, key)] in reading order. With group_min, a section is cut into groups; but a section whose
    words did not change since it was read as one part (a post read before grouping) keeps that one part, so a
    finished audio is never cut up or read again just for the new rule (user decision 2026-11-07): only a section
    read again is grouped."""
    out = []
    for h, ps in sections(txt, paras):
        whole = part_key(engine, pause_sec, ps)
        gs = groups(ps, group_min)
        keys = [part_key(engine, pause_sec, g) for g in gs]
        if len(gs) > 1 and whole in known and not all(k in known for k in keys):
            out.append((h, ps, whole))
        else:
            out += [(h if i == 0 else f"{h} ({i + 1})", g, k) for i, (g, k) in enumerate(zip(gs, keys))]
    return out


def build(txt: Path, lang: str, paras: list[str], engine: dict, sr: int, pause_sec: float, read_many, fresh=False,
          part_bitrate: str = PART_BITRATE, group_min: int = 0):
    """The whole audio and the samples of each paragraph, reading only the parts no stored part holds yet.

    read_many(list of paragraphs) yields one float32 array per paragraph, in order; it is called once, and only when
    something must be read (so the model is not even loaded when every part is reused). fresh=True reads everything.
    group_min > 0 cuts each section into groups of paragraphs (groups(), plan_parts()).
    """
    slug = txt.stem
    store = txt.parent / "parts"
    manifest_file = txt.with_name(slug + ".parts.json")
    old = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {}
    if old.get("sr") not in (None, sr):
        old = {"published": old.get("published", [])}  # another sample rate: every part is read again
    known = {p["key"]: p["lens"] for p in old.get("parts", [])}
    published = set(old.get("published", []))
    base = None
    pause_n = int(sr * pause_sec)

    plan, todo, fetched = [], [], 0
    for h, ps, key in plan_parts(txt, paras, engine, pause_sec, {} if fresh else known, group_min):
        lens = None if fresh else known.get(key)
        audio = None
        if lens and len(lens) == len(ps):
            local = store / f"{key}.opus"
            if not local.exists() and key in published:
                kept = repo_store()
                if kept is not None:
                    # audio kept in the repo: the part is in the site's public folder, or not at all (pull the repo)
                    src = kept / "parts" / f"{slug}.{lang}" / f"{key}.opus"
                    if src.exists():
                        store.mkdir(parents=True, exist_ok=True)
                        local.write_bytes(src.read_bytes())
                        fetched += 1
                    else:
                        print(f"part {key} not in {kept} (pull the repo?): reading it again", flush=True)
                else:
                    base = base or audio_base()
                    try:
                        store.mkdir(parents=True, exist_ok=True)
                        # Cloudflare's Browser Integrity Check answers the default "Python-urllib" agent with 403
                        # (error 1010, 2026-11-05): name the client.
                        req = urllib.request.Request(f"{base}/parts/{slug}.{lang}/{key}.opus", headers={"User-Agent": UA})
                        with urllib.request.urlopen(req, timeout=60) as r:
                            local.write_bytes(r.read())
                        fetched += 1
                    except (urllib.error.URLError, OSError) as e:
                        print(f"part {key} not fetched from R2 ({e}): reading it again", flush=True)
            if local.exists():
                audio = decode(local, sr, sum(lens) + pause_n * len(lens))
        if audio is None:
            lens = None
            todo += ps
        plan.append({"key": key, "h": h, "paras": ps, "audio": audio, "lens": lens})

    reused = sum(1 for p in plan if p["audio"] is not None)
    print(f"{len(plan)} part(s): {reused} reused ({fetched} fetched from the store), {len(plan) - reused} to read "
          f"({len(todo)} of {len(paras)} paragraphs)", flush=True)

    pause = np.zeros(pause_n, dtype=np.float32)
    if todo:
        wavs = iter(read_many(todo))
        for p in plan:
            if p["audio"] is not None:
                continue
            arrs = [np.asarray(next(wavs), dtype=np.float32) for _ in p["paras"]]
            p["lens"] = [len(a) for a in arrs]
            p["audio"] = np.concatenate([x for a in arrs for x in (a, pause)])
            # .tmp until the manifest holds its lengths: a run stopped half way leaves no part whose lengths the
            # manifest does not know (a new read of the same words never has exactly the same lengths).
            encode_opus(p["audio"], sr, store / f"{p['key']}.opus.tmp", part_bitrate)
            p["new"] = True
            published.discard(p["key"])  # R2 holds another read under this name (--fresh, failed fetch): upload again

    keys = [p["key"] for p in plan]
    manifest = {"v": 1, "sr": sr, "engine": engine, "pause": pause_sec,
                "parts": [{"key": p["key"], "h": p["h"], "lens": p["lens"]} for p in plan],
                # still on R2 from earlier runs; publish.mjs uploads the new ones and deletes the ones no longer used
                "published": sorted(published)}
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    for p in plan:
        if p.get("new"):
            (store / f"{p['key']}.opus.tmp").replace(store / f"{p['key']}.opus")
    full = np.concatenate([p["audio"] for p in plan])
    lengths = [n for p in plan for n in p["lens"]]
    return full, lengths, keys
