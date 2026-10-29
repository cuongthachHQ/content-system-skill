---
name: cuongthach-update
description: "Update the installed Content system skills by Cuong Thach (cuongthach and the ct-* skills) to the latest version - check for a newer release, show what changed, update on the user's yes. Use when the user types /cuongthach-update, or says update the skills, cập nhật skill, cập nhật bộ skill, có bản mới chưa, skill có gì mới."
license: CC-BY-4.0
metadata:
  author: Cuong Thach
  homepage: https://cuongthach.com/
  docs: https://cuongthach.com/docs/
---

# Update the Content system skills

Full source: https://cuongthach.com/docs/content-system/agent-skills/ (Vietnamese: https://cuongthach.com/docs/vi/content-system/agent-skills/). The skills follow the docs: when a docs page they are drawn from changes, a new version is released and listed in the CHANGELOG.

Reply in the user's language. Never update without the user's yes.

## What to do

1. **Look for a newer version.** Run `npx skills check` in the project folder. If `cuongthach` and the `ct-*` skills are up to date, say so and stop.
2. **Show what changed.** Read https://raw.githubusercontent.com/cuongthachHQ/content-system-skill/main/CHANGELOG.md (if you cannot fetch it, give the user the link https://github.com/cuongthachHQ/content-system-skill/blob/main/CHANGELOG.md). Summarize the versions newer than the installed one in a few short lines: skills added, removed or renamed first.
3. **Update on the user's yes.** Run `npx skills update`. If the skills were installed for every project (`npx skills list` shows where they are), the update covers them too.
4. **Check.** Tell the user to type `/` and look for `cuongthach` and every `ct-*` skill. Claude Code picks up the change in the open session. Other agents may need a restart. A skill that was renamed in the CHANGELOG now answers to its new name.

## What you never do

- Edit the skill files by hand, or keep an old copy next to the new one.
- Update other skills the user did not ask about.
