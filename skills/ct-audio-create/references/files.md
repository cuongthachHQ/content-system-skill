# Files of the audio tool

Read it when a command fails, a flag is unclear, or a file must be found. The steps are in `SKILL.md`.

| File | Role |
|---|---|
| `scripts/setup.sh` | One-time install on macOS or Linux (x86_64 or arm64): checks the machine, uv, Python 3.12, `vieneu`, ffmpeg, the Vietnamese model, then `kokoro-onnx` and the Kokoro model in `~/.vieneu-tts/kokoro`. Safe to run again |
| `scripts/setup.ps1` | The same for Windows 10 or 11 (PowerShell) |
| `scripts/md-to-tts-txt.py` | Any post `.md` to clean reading text. Flags: `--skip`, `--read-title`, `--no-headings`, `--chapters`, `--ordinal`, `--fix`, `--lang` (picked from the path: `/en/` is English), `--scan` (writes nothing: acronyms, English words, hyphenated words and numbered lists with their spoken form). Reads the `##` and `###` headings, not the post title; drops asides in round brackets in both languages |
| `scripts/doc-bai-viet-vieneu.py` | The Vietnamese reader: a `.txt` to an M4A, AAC 56 kbit/s mono (`--voice`, `--ref`, `--format mp3`, `--sample`, `--workers` (2 by default), `--sync`, `--no-sync`, `--fresh`, `--list-voices`) |
| `scripts/doc-bai-viet-kokoro.py` | The English reader, same text format and flags (`--voice`, default `am_michael`, `--speed`) |
| `scripts/parts.py` | Shared by both readers: one Opus 48 kbit/s part per `##` section (the opening is one too), named by the hash of engine, voice, pause and spoken text; reuses a part from `<txt folder>/parts/`, from `audio.dir/parts/` (repo store) or from `audio.base/parts/<slug>.<lang>/<hash>.opus` (R2), reads only the rest, joins them, writes `<slug>.parts.json`. `--fresh` on a reader skips it. Needs the converter's `<slug>.sections.json`, else the whole text is one part. A newly read part stays `.opus.tmp` until `parts.json` holds its lengths |
| `scripts/audio_sync.py` | Shared by both readers: writes the read-along timing file `<audioSync>/<slug>.<vi|en>.json` (start, end and the page text per paragraph) from the converter's `<slug>.src.json` |
| `scripts/stale.mjs` | Offline: which audio no longer matches its post (`.txt` vs post, audio vs post, per language), and for one slug the changed paragraphs, `--write` to redo step 3 with the last run's flags, and the exact commands of steps 4 to 6 |
| `scripts/publish.mjs` | Step 6 in one command: store the audio and its parts (R2 or the repo), check it, write the `audio:` line, delete the working audio (`--lang=en`, `--page`, `--dry`, `--keep`) |
| `scripts/doc-bai-viet-vieneu.ipynb` | The Vietnamese reader in Google Colab, nothing to install (may need fixes). Fallback when a local install is impossible |
| `lib/config.mjs` | The reader of `content.config.json` for the two Node scripts (the Python ones read the file themselves) |
| `<audioWork>/<slug>/` | Working folder: the `.txt`, its `.src.json` (page text per paragraph), `.sections.json` (paragraphs per section), `.args.json` (the converter flags, for `stale.mjs`), `.parts.json` (the parts and which are stored) and an optional `fix.tsv`; the generated audio until it is stored (`*.m4a`, `*.mp3`, `*.wav` and `parts/` belong in `.gitignore`); English in `<audioWork>/<slug>/en/`, same file names |
| `audio.dir` (repo store) or the R2 bucket | The copy the site serves: `<slug>.<vi|en>.m4a` and `parts/<slug>.<lang>/<hash>.opus`. R2 answers Range requests, so seeking works there; a static folder on Cloudflare Workers does not seek, other hosts usually do |

## After storing

- A renamed or removed post: delete its old file by hand (R2: `npx wrangler r2 object delete <bucket>/<old-slug>.vi.m4a --remote`; repo: the files under `audio.dir`).
- Keep the `.txt`, `.src.json`, `.args.json`, `.sections.json`, `.parts.json` and `fix.tsv`: they are small and remake the audio.
- Keeping R2 cheap: one file per audio with `Cache-Control: public, max-age=86400` (set by `publish.mjs`), parts cached a year under names that never change, a CDN host in front of the bucket, never the public `r2.dev` address; `publish.mjs` deletes the parts a post no longer uses.
