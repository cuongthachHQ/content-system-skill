# Your own voice on ElevenLabs

`scripts/doc-bai-viet-elevenlabs.py` reads Vietnamese and English with the voice the user cloned on ElevenLabs, through the ElevenLabs API. It replaces the reader of steps 4 and 5 of `SKILL.md`; the other steps are the same for every voice. Read this file before the first ElevenLabs read of a session, or when a run fails.

## Setting it up (the user does this once)

1. **Clone the voice** on ElevenLabs from the user's own recordings. Never clone a voice that is not the user's own or that the person did not allow.
2. **Create an API key**: Developers > API keys. Turn on "Restrict key" and allow only **Text to Speech** (Access) and **Voices** (Read; only `--list-voices` needs it). A credit limit on the key keeps a mistake cheap.
3. **Find the voice ID**: on the voice's page in ElevenLabs, or `"$PY" <skill>/scripts/doc-bai-viet-elevenlabs.py --list-voices` once the key is set (cloned voices first: id, kind, name).
4. **Write both into `.env`** at the root of the project (the folder of `content.config.json`), a file that must be in `.gitignore`:

   ```
   ELEVENLABS_API_KEY=...
   ELEVENLABS_VOICE_ID=...
   ```

   The script also reads them from the environment. If either is missing, tell the user which one to add and stop; never ask for the value in chat, never print it.
5. **Make it the default** (optional): `"engine": "elevenlabs"` in the `audio` part of `content.config.json`. `stale.mjs` then prints the ElevenLabs reader in its next commands. Without it, use ElevenLabs only when the user asks for their own voice; a post once read with ElevenLabs stays on it (its `parts.json` says so).

To change the voice later, replace `ELEVENLABS_VOICE_ID` (or pass `--voice <id>` for one read). A new voice reads every section again, since the parts are keyed on the voice.

## Defaults and flags

| Setting | Default | Flag |
|---|---|---|
| Model | `eleven_v4`, both languages | `--model` (`eleven_v3`; `eleven_flash_v2_5` costs about half; `eleven_multilingual_v2` has no Vietnamese) |
| Voice | `ELEVENLABS_VOICE_ID` | `--voice <id>` |
| Speed | Vietnamese 1.1 x, English 1.0 x | `--tempo` (applied after the call with ffmpeg `atempo`, pitch kept). v3 and v4 ignore the API's `--speed` |
| Voice settings | the voice's own | `--stability`, `--similarity` (0 to 1); `--style` only below v4, `--speed` only below v3 (the reader drops them with a notice). If the voice drifts between paragraphs, try stability 0.7 and similarity 0.5 |
| Stitching | on | `--no-stitch` (section "Stitching") |
| Sound from the API | PCM 44.1 kHz mono | `--sr 24000` on a plan that refuses 44.1 kHz |
| Audio file | HE-AAC 40 kbit/s mono (about 6 MB for 19 minutes) | none; AAC-LC 64 kbit/s (about 9 MB) when no HE-AAC encoder is found; `--format mp3` for an MP3 |
| Parts | Opus 64 kbit/s, one per group of paragraphs of at least 200 characters (section "Parts") | none |
| Requests at once | 2 | `--workers` (4 suits a batch); a 429 (the plan's concurrency limit) and 5xx errors are waited out and retried |
| Language | from the path (`.../en/<slug>.txt` is English) | `--lang` |

HE-AAC needs Apple's encoder: qaac on Windows, the Homebrew ffmpeg (`aac_at`) on macOS. Install only with the user's yes: [setup.md](setup.md), "HE-AAC". Apple's HE-AAC gives at most 40 kbit/s for one channel. ffprobe shows the file as stereo (implicit SBR signalling); it is mono.

## Commands

```bash
"$PY" <skill>/scripts/doc-bai-viet-elevenlabs.py <audioWork>/<slug>/<slug>.txt --dry      # characters to send, free
"$PY" <skill>/scripts/doc-bai-viet-elevenlabs.py <audioWork>/<slug>/<slug>.txt --sample   # paragraph 2, <slug>-thu.m4a (--sample 3: paragraphs 2 to 4, to hear the joins)
"$PY" <skill>/scripts/doc-bai-viet-elevenlabs.py <audioWork>/<slug>/<slug>.txt > <log outside the project> 2>&1   # in the background
```

The read ends with `N characters sent to ElevenLabs, M credits billed`: M is what ElevenLabs billed (the `character-cost` response header); tell the user. English: the same on `<audioWork>/<slug>/en/<slug>.txt`. On Windows prefix `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`. The last log line is `Wrote <file> (<minutes> min, <encoder>)`: check it names HE-AAC when an encoder is installed. A 20-minute post takes about 2 minutes per language with `--workers 4`. Then store it as usual (step 6).

## Cost

ElevenLabs bills credits per character sent: 1 credit per character for v4 (Flash and Turbo models about 0.5). The sample rate, the tempo and the encoding cost nothing. Always run `--dry` before a whole read and tell the user the count.

- A post of 12,000 to 14,000 characters per language is about 26,000 credits in two languages.
- A redo after an edit sends only the sections whose words changed (the parts), usually a few hundred to a few thousand characters.
- A sample is about 300 characters.
- Credits of a monthly plan usually do not roll over: the saving is a plan that fits the posts a month.

## Parts

The ElevenLabs reader cuts each section into groups of consecutive paragraphs of at least 200 characters, never across a section; a short heading or line joins the paragraph after it, a short tail joins the group before it. A few words changed then send about 280 characters again instead of the whole section (often over 1,000). v4 reads every paragraph on its own anyway, so a group read again sounds like the rest. A section stored whole (read before this rule, or by an older version) keeps that part while its words stay the same; its first edit reads the section whole and stores it in groups. A post has about 45 parts per language; the store holds the same seconds of sound, so its size does not change.

## Stitching

Every paragraph is sent with the paragraph before and after it (`previous_text` and `next_text`), so the tone carries across paragraphs instead of each one starting fresh. The context is not billed: the same paragraphs cost the same credits with and without it. `--no-stitch` turns it off.

Stitching is part of a part's name, but a part read without it is reused while its words stay the same: audio read before is never read again just for stitching, and an edit reads only the changed groups, stitched. Read a post again whole (`--fresh`) only with the user's yes.

## Known pitfalls

- `eleven_multilingual_v2` cannot read Vietnamese.
- v3 and v4 read words in square brackets as audio tags (`[whispers]`, `[laughs]`): the reader removes every `[` and `]` before sending to them.
- An error names its likely cause: 401 the key, 402 the plan or the credits, 404 the voice id, 422 a refused parameter.
- A key without Models permission answers 401 `missing_permissions` on the model list: not needed for reading.
- Raising `--speed` does nothing on v3 and v4: use `--tempo`.
