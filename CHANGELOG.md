# Changelog

Each release follows the docs at https://cuongthach.com/docs/. A skill changes only when the docs page it is drawn from changes.

## 0.3.2 - 2026-11-12

- `LICENSE` is now the standard CC BY 4.0 text, so GitHub shows the license by name; the credit line and the note on method names stay in the README. Both READMEs and the docs page count 9 skills, `cuongthach-update` included. No skill changed.

## 0.3.1 - 2026-11-08

- The docs page lists `ct-repost-write` in its own section with a demo picture, and the install troubleshooting now sits under the install steps. No skill changed.

## 0.3.0 - 2026-11-08

- New skill `ct-repost-write`: repurposes a published post into versions for other channels (newsletter, Facebook or X post, community question, videos, podcast), keeping every idea, one idea per version, each linking back to the post. Each version gets a new illustration for the idea of one H2, painted in ink and watercolour with one or two labels of one or two words. `cuongthach` routes a published post to it; both READMEs and the docs page list it.

## 0.2.2 - 2026-11-07

- `ct-audio-create` keeps smaller parts with ElevenLabs: each section is cut into groups of paragraphs of at least 200 characters, so a few words changed send about 280 characters again instead of the whole section. Audio already made keeps its parts until a section is edited. The docs page has the new row in its comparison table.

## 0.2.1 - 2026-11-07

- `ct-audio-create` can read with your own voice cloned on ElevenLabs, Vietnamese and English with the Eleven v4 model, through a new reader script; `references/elevenlabs.md` explains the API key, the voice ID, the defaults (Vietnamese 1.1 x faster with the pitch kept, HE-AAC 40k from 44.1 kHz sound) and the cost, and `"engine": "elevenlabs"` in the config makes it the default. The scripts also cut a long H2 into one part per H3, so an edit re-reads less. `cuongthach` and both READMEs mention the new voice; `cuongthach-update` had only wording changes in its docs.

## 0.2.0 - 2026-11-05

- New tool skill `ct-audio-create`: reads a finished post aloud with two voices that run on your own computer (VieNeu-TTS for Vietnamese, Kokoro for English), one audio part per section so an edit re-reads only that section, the M4A kept in Cloudflare R2 or in your repo. The first skill with scripts; `cuongthach` routes a finished post to it, both READMEs and the docs page list it, and the install needs about 10 minutes and 2 GB once for the voices.

## 0.1.3 - 2026-11-05

- `ct-profile-create` now says Product and Website are the 2 required entries and the other 8 can stay empty, as the brand profile docs do. The other skills had only wording changes in their docs, so they stay as they are.

## 0.1.2 - 2026-11-02

- `ct-message-create` rewritten after the docs: the core message is one line squeezed from four parts of context (customer, pain in three layers, solution, result), made after the ideas are out and checked with four questions; no more six options. `cuongthach`, `ct-record-plan`, `ct-post-write` and `ct-post-classify` follow the same docs changes in a line or two each.

## 0.1.1 - 2026-10-30

- Renamed to Content System Skills by Cuong Thach, and each README opens with a 40-second video of the skills (English and Vietnamese).

## 0.1.0 - 2026-10-29

- First release: the master skill `cuongthach` and five `ct-*` skills (`ct-profile-create`, `ct-post-classify`, `ct-record-plan`, `ct-message-create`, `ct-post-write`), and `cuongthach-update` to update them.
