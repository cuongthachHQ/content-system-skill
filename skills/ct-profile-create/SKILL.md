---
name: ct-profile-create
description: "Help the user fill their own brand profile from Cuong Thach's ten-entry template (brand, product, readers, pain, what sets you apart, true stories, own names, voice, website, docs), asking one entry at a time and never inventing data. Use when the user says brand profile, hồ sơ thương hiệu, wants to set up before writing content, or another ct-* skill needs their readers, voice or product."
license: CC-BY-4.0
metadata:
  author: Cuong Thach
  homepage: https://cuongthach.com/
  docs: https://cuongthach.com/docs/
---

# Brand profile (Hồ sơ thương hiệu)

A template by Cuong Thach. Full source: https://cuongthach.com/docs/content-system/resources/brand-profile-template/ (Vietnamese: https://cuongthach.com/docs/vi/content-system/resources/brand-profile-template/). Why each entry matters: https://cuongthach.com/docs/content-system/conditions/brand-profile/. When this skill and the docs disagree, the docs win.

Reply in the user's language. A writer or AI agent reads this profile before any content work, so every entry must be the user's real data.

## How to fill it

1. Ask where to save the file (suggest `brand-profile.md` at the project root). If one exists, read it and fill only the gaps.
2. Go through the ten entries **one at a time**, in order. For each, say in one line which part of the work uses it, then ask.
3. Write the user's answer in their own words. **Never invent, guess or polish data.** An entry with no data gets `Not yet`, and the line stays.
4. Each true story must be one the user may share.
5. At the end, show the filled file and list the entries still `Not yet`.

| Entry | Used by | What to ask |
|---|---|---|
| Brand | Every post | One brand name and the person behind it |
| Product | The Love post's end point | Name, what buyers get, status (on sale or taking a waitlist). An unfinished product is fine: status "taking a waitlist" |
| Readers | Topic choice, the Reader line of every question set | One specific group, not everyone |
| Pain | The Know post | The long-running problem, in the readers' own words |
| What sets you apart | The Love post | Strengths, skills, experience of the person behind the product, one per line |
| True stories | The Write step | What happened, when, how it turned out |
| Own names | The Edit step | Each name and its fixed translation; never changed for SEO |
| Voice | The Edit step | First language, how readers are addressed, how much spoken style, words never used |
| Website | Every post is published here first | Domain, sales page, waitlist page |
| Docs | Facts for posts | Docs address, Method, Common questions (`Not yet` if missing) |

## Template

```markdown
# Brand profile: <brand name>

## Brand
- Name: <brand name>
- Person behind it: <person's name>

## Product
- Name: <product name>
- Includes: <what buyers get>
- Status: <on sale | taking a waitlist>

## Readers
- <specific group of people>

## Pain
- <long-running problem, in the readers' own words>

## What sets you apart
- <strength, skill or experience 1>
- <strength, skill or experience 2>

## True stories
- <story 1: what happened, when, how it turned out>
- <story 2>

## Own names
- <name> = <fixed translation>

## Voice
- Language: <language you write in first>
- Addressing readers: <how you address readers>
- Spoken style: <keep some | keep to a minimum>
- Never use: <words or kinds of sentences>

## Website
- Address: <domain>
- Sales page: <link>
- Waitlist page: <link or Not yet>

## Docs
- Docs address: <link>
- Method: <link>
- Common questions: <link>
```
