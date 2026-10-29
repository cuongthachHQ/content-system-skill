<div align="center">

**English** · [Tiếng Việt](README.vi.md)

# Content System Skills by Cuong Thach

**Idea - Write - Edit · Know - Trust - Love content funnel · Core message**

7 skills that let your AI agent walk you through one post with Idea - Write - Edit, from brand profile to edited draft, without writing for you. Built from [Cuong Thach](https://cuongthach.com/)'s content method.

[![GitHub stars](https://img.shields.io/github/stars/cuongthachHQ/content-system-skill?style=social)](https://github.com/cuongthachHQ/content-system-skill/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cuongthachHQ/content-system-skill?style=social)](https://github.com/cuongthachHQ/content-system-skill/network/members)
[![Last commit](https://img.shields.io/github/last-commit/cuongthachHQ/content-system-skill)](https://github.com/cuongthachHQ/content-system-skill/commits)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)

[Homepage](https://cuongthach.com/) · [Docs](https://cuongthach.com/docs/) · [Install guide](https://cuongthach.com/docs/content-system/agent-skills/) · [Blog](https://cuongthach.com/blog/)

</div>

---

Each skill is a folder of instructions that an AI agent loads when your task calls for it. These skills bring the Idea - Write - Edit process into your agent. They:

- Fill in your brand profile with you
- Sort a post into a Know, Trust or Love post
- Write recording questions
- Squeeze the core message
- Walk you through locking the outline, writing and editing

**The ideas and the words are still yours to write.**

## What you need

- [Claude Code](https://code.claude.com/docs/en/overview) or [Antigravity](https://antigravity.google/), open in the project folder where you make content
- The latest LTS version of [Node.js](https://nodejs.org/en/download). The install command runs with `npx`, which comes with Node.js, and needs **at least version 22.20**

## Install in your agent

**1. Install the 7 skills.** The fastest way is to paste this into your agent, and it runs the install command:

```text
Install all skills from https://github.com/cuongthachHQ/content-system-skill into this project with npx skills add, picking the agent you are running and adding -y, then list the installed skills.
```

Or run the command yourself in a terminal, in your project folder:

```bash
# Claude Code
npx skills add cuongthachHQ/content-system-skill --skill '*' -a claude-code -y

# Antigravity
npx skills add cuongthachHQ/content-system-skill --skill '*' -a antigravity -y
```

Add `-g` to the end of the command to use the skills in every project on your computer.

**2. Check the skills are in the agent.**

- **In Claude Code**, type `/` and see all 7 names, in `.claude/skills/`.
- **In Antigravity**, ask *"Which skills do you have?"*, with the skills in `.agents/skills/`.

**3. Type `/cuongthach`.** The main skill asks what you hold: a topic, a recording, a locked outline or a draft. You answer, then it runs the skill for the next step, **without writing the post on its own**.

## What is included

| Skill | What it does |
|---|---|
| `cuongthach` | The main skill: sees which step a post is at, hands the next step to the right skill, and does no step itself |
| `ct-profile-create` | Fills in your 10-entry brand profile with you, one entry at a time, writing `Not yet` for an empty entry |
| `ct-post-classify` | Sorts a post into exactly one type: Know post, Trust post or Love post |
| `ct-record-plan` | Writes a question set in three groups, What it is, How it works, Why it matters, for you to answer while you record |
| `ct-message-create` | Squeezes three answers about the customer, the problem and the solution into one core message |
| `ct-post-write` | Runs the three steps of Idea - Write - Edit: lock the outline, write the draft in one go, then only cut |
| `cuongthach-update` | Checks for a newer version of the skills, sums up what changed, and updates them on your yes |

## Skill usage examples

A post goes through the skills in the order below. **You only need to type `/cuongthach`** and the agent calls the next step, or type a skill's name when you know which step you are at.

- `/ct-profile-create`: fill in the 10-entry brand profile, once
- `/ct-post-classify Is this a Know, Trust or Love post?`: sort the post before you write
- `/ct-record-plan A Trust post on writing from a recording`: get the questions to record with
- `/ct-message-create`: paste the recording and squeeze it into one core message
- `/ct-post-write`: filter ideas, lock the outline, then write and edit

You can also say the task in plain words, such as *"Which step is this post at?"*, and the agent calls the skill whose description matches.

## Update Skills

**The skills follow the docs**: when a docs page that a skill is drawn from changes, a new version is released and listed in [CHANGELOG.md](CHANGELOG.md).

**Use `/cuongthach-update`.** The agent checks for a newer version, sums up what changed for you to read, and updates on your yes. Without an agent, run `npx skills update` in your project folder.

## When the install goes wrong

<details>
<summary>The npx command fails</summary>

This is usually a Node.js version older than 22.20: **install the latest LTS version** and run the command again. If it still fails, install by hand: download this repo's ZIP and copy each folder inside `skills/` into `.claude/skills/` for Claude Code or `.agents/skills/` for Antigravity.
</details>

<details>
<summary>The agent does not see the skills</summary>

The agent is open in a different folder from where you installed. Open it in the project folder, or install again with `-g`.
</details>

<details>
<summary>The agent writes a post when you type /cuongthach</summary>

The skill is not loaded. Check the list of skills again, and run the install command again if a name is missing.
</details>

## Roadmap

Planned skills, each one built from a docs page that already exists. Star ⭐ and **Watch** the repo to hear when a new skill ships.

| Planned skill | What it will do | Source docs page |
|---|---|---|
| `ct-post-edit` | Turn a rough draft into a post and keep the outline as it is | [Edit a draft](https://cuongthach.com/docs/content-system/idea-write-edit/guides/tutorials/edit-a-draft/) |
| `ct-page-write` | Build a short sales page: name, proof, payment | [Build a lean sales page](https://cuongthach.com/docs/content-system/know-trust-love/guides/how-to/build-a-lean-sales-page/) |
| `ct-docs-write` | Start a Truth vault from what you already have | [Build the first vault](https://cuongthach.com/docs/content-system/truth-vault/guides/tutorials/build-the-first-vault/) |

## Source

Everything in these skills is drawn from Cuong Thach's public docs. When a skill and the docs disagree, **the docs are right**:

- [The Idea - Write - Edit process](https://cuongthach.com/docs/content-system/idea-write-edit/introduction/)
- [The Know - Trust - Love content funnel](https://cuongthach.com/docs/content-system/know-trust-love/introduction/)
- [Create a core message](https://cuongthach.com/docs/content-system/idea-write-edit/guides/how-to/create-a-core-message/)
- [AI and prompts](https://cuongthach.com/docs/content-system/resources/ai-and-prompts/)
- [Brand profile template](https://cuongthach.com/docs/content-system/resources/brand-profile-template/)

## License

© 2026 Cuong Thach ([cuongthach.com](https://cuongthach.com/)). Released under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

You may use, change and share these skills, even commercially, as long as you **give credit** like this:

```text
Based on Content System Skills by Cuong Thach (https://cuongthach.com/), licensed under CC BY 4.0.
```

**Method names:** "Content system", "content funnel", "Know - Trust - Love" and "Idea - Write - Edit", with their Vietnamese originals "Hệ thống nội dung", "Phễu nội dung", "Biết - Tin - Yêu" and "Ý - Viết - Sửa", are the names of Cuong Thach's method. When you use them, keep them as they are and credit the source. Do not use them to suggest that Cuong Thach backs your product.

## Support

If these skills help you, star ⭐ the repo at the top of the page. Each star helps other people find the method.

[![Star History Chart](https://api.star-history.com/svg?repos=cuongthachHQ/content-system-skill&type=Date)](https://star-history.com/#cuongthachHQ/content-system-skill&Date)
