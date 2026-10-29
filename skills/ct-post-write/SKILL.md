---
name: ct-post-write
description: "The Idea - Write - Edit process (Ý - Viết - Sửa) by Cuong Thach - three steps in a fixed order, each with its own stopping point - lock the outline, write the rough draft in one go, then only cut. Use when the user is outlining, writing or editing one post, or mentions Idea - Write - Edit, Ý - Viết - Sửa, outline, dàn ý, rough draft, bản nháp, or editing a draft. Called by the cuongthach master skill."
license: CC-BY-4.0
metadata:
  author: Cuong Thach
  homepage: https://cuongthach.com/
  docs: https://cuongthach.com/docs/
---

# Idea - Write - Edit (Ý - Viết - Sửa)

A method by Cuong Thach. Full source: https://cuongthach.com/docs/content-system/idea-write-edit/introduction/ (Vietnamese: https://cuongthach.com/docs/vi/content-system/idea-write-edit/introduction/). When this skill and the docs disagree, the docs win.

Reply in the user's language. Keep the protected names exactly: **Idea - Write - Edit** (Ý - Viết - Sửa), **Know - Trust - Love** (Biết - Tin - Yêu). Never reword them. When a step is done, hand control back to the `cuongthach` master skill.

## The rule

The next step starts only once the user **holds what the step before made**. Never skip a step, never run two at once.

| Step | The user's role | What they do | What they hold at the stopping point |
|---|---|---|---|
| Idea | Screenwriter | Pour out every idea, pick ideas by the core message, lock the outline | A locked outline: the post title and six to eight big ideas with short titles |
| Write | Actor | Say or write everything they understand about each idea, internet off | A rough draft, the longest version of the post |
| Edit | Editor | Tighten the opening, cut, put it in the customer's words | A finished post: they understand it, the customer understands it, they like it |

Every post type, Know, Trust or Love, goes through the same three steps. Only the shape of the outline and the opening change with the type.

## Idea step

- Start from the three root questions: **What is it? How does it work? Why does it matter** to the user and to their customers? If the user cannot answer them, they do not know the topic well enough yet: drop the post or learn more first.
- The user pours out 20 to 50 ideas. You may group them and split them into separate ideas. You never think up or pick ideas for them.
- Filter every idea by the core message (`ct-message-create`): keep what serves it, save the rest on a "for other posts" list. The core message is the filter, **not a section of the post**.
- Each kept idea gets a short, plain title: no fancy words, no slang, no metaphors.
- Order the ideas by type: Know explains so the reader understands, Trust follows the steps of the job, Love follows the strategy and the reasons.
- An outline has **no opening**. Lock it when the user reads it top to bottom and sees the message, the ideas flow, and they like it. From then on the big idea titles never change.
- Before the Write step, the user looks over the outline for ideas they only half understand and studies them first.

## Write step

- Internet off, nothing looked up, one go from the outline. No polishing, no persuading, no keywords.
- Talking beats typing for most people: they read each guiding question (`ct-record-plan`) and answer it out loud, and AI only turns speech into text. They do not listen back.
- An idea where they get stuck is one they do not understand well enough yet: note it, go on, study it later.

## Edit step

Work in this order: the opening, the main content, the ending that leads readers on.

- The user types the opening and the ending themselves: the opening needs empathy, which only a person has.
- Only cut. Put expert words into the customer's words, cut repeats and parts only the writer understands, split long sentences. **Never make the customer think.**
- Never change the big idea titles. To change the ideas, go back to the Idea step.
- A post that is too short is missing ideas, not words: add ideas in the Idea step.
- Cut ideas are not lost: save them for another post.

AI may reorder the draft by the outline, cut filler words and point out repeats. It never invents ideas, numbers or stories, and never changes the user's voice. The user is the final reviewer.

## Read more

- The Idea step: https://cuongthach.com/docs/content-system/idea-write-edit/idea/
- The Write step: https://cuongthach.com/docs/content-system/idea-write-edit/write/
- The Edit step: https://cuongthach.com/docs/content-system/idea-write-edit/edit/
- AI and prompts: https://cuongthach.com/docs/content-system/resources/ai-and-prompts/
