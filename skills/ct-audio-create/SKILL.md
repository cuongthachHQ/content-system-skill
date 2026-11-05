---
name: ct-audio-create
description: "Turn a finished post into its audio version with two voices that run on your own computer, Vietnamese (VieNeu-TTS) and English (Kokoro): clean reading text from the Markdown file, a short sample for you to approve, one audio part per section so an edit re-reads only that section, then the M4A kept in Cloudflare R2 or in the repo. Use when the user wants an audio version of a post, a read-aloud post, tạo audio, bản nghe, or to redo the audio after editing the words."
license: CC-BY-4.0
metadata:
  author: Cuong Thach
  homepage: https://cuongthach.com/
  docs: https://cuongthach.com/docs/
  kind: tool
---

# Audio version of a post (Bản nghe)

A tool skill by Cuong Thach: unlike the other skills of this set it carries scripts, because a voice cannot be described, only run. Full source: https://cuongthach.com/docs/content-system/agent-skills/ (Vietnamese: https://cuongthach.com/docs/vi/content-system/agent-skills/). When this skill and the docs disagree, the docs win.

Reply in the user's language. The audio is made only from a post the user calls final (the Edit step of **Idea - Write - Edit**, Ý - Viết - Sửa, is done): audio read from words that will change must be read again.

| Language | Engine | Voice |
|---|---|---|
| Vietnamese | **VieNeu-TTS v3 Turbo** (Apache-2.0, 25 Vietnamese voices, optional cloning from the user's own 3 to 8 second clip) | ask the user once, then keep it for every post |
| English | **Kokoro-82M** v1.0 through `kokoro-onnx` (Apache-2.0) | `am_michael` |

Both run on the CPU, nothing leaves the computer. Never read English with VieNeu or Vietnamese with Kokoro.

## What you need

1. **The skill folder**, installed with the other skills: `<skill>` below is `.claude/skills/ct-audio-create` (Claude Code) or `.agents/skills/ct-audio-create` (Antigravity).
2. **One Python environment**, built once per computer by the installer (step 1 below): `PY` is `~/.vieneu-tts/.venv/bin/python` on macOS and Linux, `%USERPROFILE%\.vieneu-tts\.venv\Scripts\python.exe` on Windows (PowerShell: `& $Py script args`); `VIENEU_HOME` moves the folder. Every command below runs on `PY`, never on the system Python.
3. **A config file** `content.config.json` at the root of the project, read by every script (nearest one above the skill folder):

```json
{
  "kit": "content-kit",
  "site": { "name": "my-site", "domain": "example.com", "defaultLang": "vi", "langs": ["vi", "en"] },
  "paths": {
    "blog": "posts",
    "audioWork": "audio-work",
    "audioSync": "public/audio-sync"
  },
  "audio": {
    "dir": "public/audio",
    "base": "/audio",
    "voice": "Thiện Minh"
  }
}
```

- `paths.blog`: the Markdown posts, one folder per language, `<blog>/<lang>/<slug>.md` (`paths.pages` the same for content pages, optional). A WordPress site keeps a Markdown copy of each post there and uploads the finished M4A to its Media Library by hand.
- `paths.audioWork`: the working folder of a read (the reading text, its small JSON files, the audio until it is stored); `paths.audioSync`: the read-along timing files, one per audio (the site's player may use them; harmless otherwise).
- `audio`: where the finished audio lives. **In the repo**: `dir` (a folder the site serves) and `base` (the address it is served at, or a placeholder). **In Cloudflare R2**: `bucket` and `base` (the public address of the bucket) instead of `dir`; `purgeCommand` (optional) is the site's own command that purges one URL, with `{url}` in it. `voice`: the Vietnamese voice, once chosen.

## Steps

1. **Check the install.** `"$PY" -c "from vieneu import Vieneu; import kokoro_onnx"` works and `~/.vieneu-tts/kokoro/voices-v1.0.bin` exists? If not: read [references/setup.md](references/setup.md) and follow it (the installer per system, what gets installed and where, troubleshooting). Nothing outside its list is ever installed.
2. **Pick the post.** `<blog>/vi/<slug>.md` (English: `<blog>/en/<slug>.md`, the Kokoro reader, `--lang=en`). The file needs `##` headings for its sections; the title line is not read (`--read-title` reads it). Vietnamese voice: `audio.voice` of the config, else ask once (`"$PY" <skill>/scripts/doc-bai-viet-vieneu.py --list-voices`) and write it there. The user's own voice: a 3 to 8 second clean clip (`--ref`); never clone anyone else's.
3. **Scan before reading:** `"$PY" <skill>/scripts/md-to-tts-txt.py <blog>/vi/<slug>.md --scan` with the flags you plan (`--ordinal`, `--fix`, `--skip`); it writes nothing and lists acronyms, English words, hyphenated words and every numbered list with the lead it will get ("Bước một", "Thứ nhất" or plain). Show the doubtful items and ask, per numbered list: steps (Bước), ideas or questions (`--ordinal`), or plain (`<!-- not-steps -->` above it in the post). Then **make the text**: `"$PY" <skill>/scripts/md-to-tts-txt.py <blog>/vi/<slug>.md <audioWork>/<slug>`. Numbers, percentages, money, tables, lists, links and symbols become words; code blocks and asides in round brackets are not read. Flags: `--skip "<H2 text>"` drops a section (a closing call to action); `--ordinal` for essays and lists of ideas, the default "Bước" for how-to posts; `--fix <audioWork>/<slug>/fix.tsv` respells words the voice says wrong (`written<TAB>spoken`, matched against the converted text, never the Markdown). English: the same with `<blog>/en/<slug>.md <audioWork>/<slug>/en`. What the converter already handles: [references/text-rules.md](references/text-rules.md). On a first read, read the whole `.txt` once; never rewrite the author's sentences.
4. **Sample first:** `"$PY" <skill>/scripts/doc-bai-viet-vieneu.py <audioWork>/<slug>/<slug>.txt --voice "<voice>" --sample` writes `<slug>-thu.m4a` (paragraph 2). We cannot listen: ask the user to, and name the words to check (brand names, new acronyms). A word read wrong goes to `fix.tsv` with the user's OK; rerun step 3 and the sample. English: `<skill>/scripts/doc-bai-viet-kokoro.py <audioWork>/<slug>/en/<slug>.txt --sample`.
5. **Read the whole post in the background:** same command without `--sample`, log to a file outside the project, run as a background command and wait for its notification (the log ends with `Wrote` or a `Traceback`); read only the log's tail. On Windows prefix `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`. Output: `<audioWork>/<slug>/<slug>.m4a` (AAC 56 kbit/s mono, about 7 MB for 18 minutes; a 30-minute post reads in about 9 minutes on an Apple chip) plus the timing file in `<audioSync>`. The reader keeps one Opus part per `##` section in `parts/` and lists them in `<slug>.parts.json`; it reads only the sections no part holds (`--fresh` reads all). One post at a time, never split across subagents (the voice uses every core).
6. **Store it:** `node <skill>/scripts/publish.mjs <slug>` (English `--lang=en`, a content page `--page`, `--dry` shows the plan, `--keep` keeps the local file). It refuses a sample or a missing file; stores the new parts first, then the joined file (R2: upload, purge, a size check past the cache; repo: a copy into `audio.dir`, size checked); writes `audio: "<base>/<slug>.<lang>.m4a"` into the post's frontmatter (after `cover:`); removes parts no longer used; deletes the working audio. Redoing an audio replaces the old file under the same name, never a `-2` name. Commit `<slug>.parts.json`, the timing file and, in the repo store, `audio.dir` with the post: another machine needs them to reuse the parts.
7. **Finish.** Tell the user the file, its size and minutes, where it is, and what still needs their ears. A WordPress site: upload the M4A to the Media Library and place an Audio block under the post's cover; a redo replaces that media file.

**Redoing audio after the words changed:** `node <skill>/scripts/stale.mjs` (every audio, one table) or `stale.mjs <slug> [--lang=vi|en]` (the changed paragraphs and the exact next commands); `--write` does step 3, then go on from step 4. Step 5 re-reads only the sections whose words changed and joins them with the other parts (taken back from the store when this computer lacks them), so a small edit takes seconds. Read only the changed paragraphs it prints, never the whole text again.

## Never

- Never clone a voice that is not the user's own or that the person did not allow.
- Never run a whole read in the foreground, on the system Python, or with two readers at once.
- Never upload WAV or MP3, a sample, or a higher bitrate; one file per audio, replaced under the same name.
- Never install anything outside the list in `references/setup.md`, and never put it in the project or the system Python.
