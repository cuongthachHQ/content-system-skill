---
name: ct-record-plan
description: "Write a set of guiding questions the user reads aloud and answers while recording a post (talk to write), by Cuong Thach's method - three groups (What it is, How it works, Why it matters), the group of the post type goes deepest, questions only, never answers. Use when the user wants to record a post, asks for recording questions, câu hỏi ghi âm, an interview script for themselves, or says they do not know what to say."
license: CC-BY-4.0
metadata:
  author: Cuong Thach
  homepage: https://cuongthach.com/
  docs: https://cuongthach.com/docs/
---

# Recording question set (Bộ câu hỏi ghi âm)

A method by Cuong Thach. Full source: https://cuongthach.com/docs/content-system/resources/ai-and-prompts/ (Vietnamese: https://cuongthach.com/docs/vi/content-system/resources/ai-and-prompts/). When this skill and the docs disagree, the docs win.

Reply in the user's language and write the questions in the language they will record in. This set belongs to the Idea step of **Idea - Write - Edit** (Ý - Viết - Sửa): Cuong calls it the **idea-starter structure**. It guides what the user will say; the sharp outline only exists after the recording.

## What you need

- **A one-line topic.**
- **The post type:** Know, Trust or Love. If the user does not know, use the `ct-post-classify` skill first.
- **The reader:** who they are and what problem they have. If the user has a brand profile, take its Readers line word for word.

## How to write the set

Play a busy, hard-to-please customer of the user.

1. **Three groups, in this order:** I. What it is, II. How it works, III. Why it matters and what you get if it works.
2. **The group of the post type goes deepest:** Know is group I (explain so the customer understands), Trust is group II (each step of the job), Love is group III (strategy, process and meaning). Ask each main idea as a chain of two or three questions, each deeper than the last.
3. **Number of questions:** ask the user how many. Cuong's current sets are about 16 for a Know post, 26 for a Trust post, 36 for a Love post. That is not a standard.
4. **Each question is short, direct, one idea.** Under each one, add one short line in the reader's voice with one concrete detail.
5. **A few questions about the user's own story:** the first time, a mistake, a turning point, a view of their own. Keep them open and never guess the answer.
6. **Only ask.** Never answer for the user and never make up their experience.

## Check the result

Usable when it has all three groups, the group of the post type is the longest, it holds only questions, and it has a few questions about the user's own story.

Tell the user how to use it: paste it on the phone or in front of the screen, read a question, then talk. Skip a question they cannot answer, say so when they do not remember clearly, and note those questions to study later. **Going blank is normal.**

If the user cannot answer the three root questions (what it is, how it works, why it matters), they do not know the topic well enough yet: drop the post or learn more first.

With no AI at hand, the three root questions alone are enough to start.

## After recording

The transcript goes to the core message (`ct-message-create`), then the ideas are filtered into an outline (`cuongthach` skill, Idea step).

## Read more

- The Write step and talk to write: https://cuongthach.com/docs/content-system/idea-write-edit/write/
- Outline from one line: https://cuongthach.com/docs/content-system/idea-write-edit/guides/tutorials/outline-from-one-line/
