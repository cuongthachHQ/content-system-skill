"""Timing file shared by both readers (doc-bai-viet-vieneu.py, doc-bai-viet-kokoro.py): when each paragraph of an
audio starts and ends, with the start of its text as the page shows it, so the site's audio player can highlight the
block being read (custom/media/AudioPlayer.astro fetches it on the first play).

Format: {"v": 1, "txt": <first 12 hex of the sha1 of the .txt read>, "segs": [[start, end, page text], ...]}, seconds
rounded to 0.01, one entry per paragraph of the .txt. "txt" lets stale.mjs tell exactly whether the audio still matches
the post (the player ignores it).
The page texts come from the converter's <name>.src.json (md-to-tts-txt.py), written beside the .txt.
"""
import hashlib, json
from pathlib import Path


def sync_dir() -> Path:
    """paths.audioSync of content.config.json (the nearest one above this file), the folder of the timing files."""
    here = Path(__file__).resolve().parent
    for d in [here, *here.parents]:
        cfg = d / "content.config.json"
        if cfg.exists():
            rel = (json.loads(cfg.read_text(encoding="utf-8")).get("paths") or {}).get("audioSync")
            if not rel:
                raise SystemExit("content.config.json has no paths.audioSync (the folder of the timing files)")
            return d / rel
    raise SystemExit(f"no content.config.json above {here}")


def sync_path(txt: Path, lang: str, override: str | None = None) -> Path:
    """<audioSync>/<name>.<lang>.json, the name the player derives from <name>.<lang>.m4a."""
    return Path(override) if override else sync_dir() / f"{txt.stem}.{lang}.json"


def write_sync(txt: Path, lengths: list[int], sr: int, pause_sec: float, out: Path) -> None:
    """lengths: samples per paragraph, in order; a pause of pause_sec follows each one. Skipped with a notice if the
    .src.json is missing or does not match the paragraphs (the audio itself is still fine)."""
    page = txt.with_name(txt.stem + ".src.json")
    if not page.exists():
        print(f"no {page.name}: no timing file (rerun md-to-tts-txt.py)", flush=True)
        return
    texts = json.loads(page.read_text(encoding="utf-8"))
    if len(texts) != len(lengths):
        print(f"{page.name} has {len(texts)} entries for {len(lengths)} paragraphs: no timing file", flush=True)
        return
    segs, t = [], 0.0
    for text, n in zip(texts, lengths):
        segs.append([round(t, 2), round(t + n / sr, 2), text])
        t += n / sr + pause_sec
    out.parent.mkdir(parents=True, exist_ok=True)
    txt_hash = hashlib.sha1(txt.read_text(encoding="utf-8").encode("utf-8")).hexdigest()[:12]
    out.write_text(json.dumps({"v": 1, "txt": txt_hash, "segs": segs}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(segs)} blocks)", flush=True)
