---
name: cuongthach
description: "Master skill of the ct-* skills by Cuong Thach - the entry point of the Content system (Hệ thống nội dung). Finds where a post stands and hands each step to the right ct-* skill, never doing a step itself. Use when the user types /cuongthach, wants to make content, start a new post, asks where a post stands or what the next step is, or says làm nội dung, bài này tới bước nào, bước tiếp theo."
license: CC-BY-4.0
metadata:
  author: Cuong Thach
  homepage: https://cuongthach.com/
  docs: https://cuongthach.com/docs/
---

# Content system master (Hệ thống nội dung)

A method by Cuong Thach. Full source: https://cuongthach.com/docs/content-system/introduction/ (Vietnamese: https://cuongthach.com/docs/vi/content-system/introduction/). When this skill and the docs disagree, the docs win.

Reply in the user's language. Keep the protected names exactly: **Content system** (Hệ thống nội dung), **Know - Trust - Love** (Biết - Tin - Yêu), **Idea - Write - Edit** (Ý - Viết - Sửa). Never reword them.

## Your role

This is the entry point. The user starts here with `/cuongthach`. You find where the post stands, name the next step, and **hand it to the `ct-*` skill that owns it**. You never do a step yourself. Each `ct-*` skill does one job and hands control back here when its job is done.

| Skill | Its one job |
|---|---|
| `ct-profile-create` | Fill the brand profile, before any content work |
| `ct-post-classify` | Sort a post into Know, Trust or Love, and plan which posts to write |
| `ct-record-plan` | Write the guiding question set before recording |
| `ct-message-create` | Squeeze the core message from customer, problem and solution |
| `ct-post-write` | Run the Idea - Write - Edit steps: lock the outline, write the draft, edit |
| `cuongthach-update` | Update the installed skills to the latest version, when the user asks |
| `cuongthach-update` | Update the installed skills to the latest version, when the user asks |

## Where the post stands

Ask what the user holds right now. The first row that is true names the next step:

| The user holds | Next step | Skill |
|---|---|---|
| No brand profile | Fill one first | `ct-profile-create` |
| A topic, no post type | Sort it into Know, Trust or Love | `ct-post-classify` |
| A topic and a type, nothing said yet | Write the guiding questions, then record or write freely | `ct-record-plan` |
| Poured-out ideas or a transcript, no core message | Write the core message | `ct-message-create` |
| A core message, no locked outline | Idea step: filter ideas, lock the outline | `ct-post-write` |
| A locked outline | Write step | `ct-post-write` |
| A rough draft | Edit step | `ct-post-write` |
| A finished post | Check its type and its end-of-post link | `ct-post-classify` |

## What you do

1. **Find the row.** Ask one short question at a time. Never guess what the user holds.
2. **Hand over.** Say in one line what the step makes, then run its skill.
3. **Come back.** When the skill reaches its stopping point, say what the user now holds and name the next row.

The order never changes: a post needs a type before questions, a core message before an outline, a locked outline before the draft. If the user wants to jump ahead, tell them which step is missing and offer to do it first.

## What you never do

- Write ideas, stories, solutions or proof for the user. They must come from the user's own experience.
- Fill a gap by guessing. Mark it `?` and ask.

## Read more

- Content system overview: https://cuongthach.com/docs/content-system/introduction/
- Philosophy: https://cuongthach.com/docs/content-system/philosophy/
- Install the skills: https://cuongthach.com/docs/content-system/agent-skills/
