#!/usr/bin/env node
// Which audio no longer matches its words, and the remake of one, offline (no network, no model, no audio made).
//
//   node <skill>/scripts/stale.mjs                 every post and page with an audio: line
//   node <skill>/scripts/stale.mjs <slug> [--lang=vi|en] [--write]
//
//   <slug>   one post or page: the paragraphs that changed (- read now, + to read) and the exact next commands
//   --lang   vi or en (default: both that have an audio: line)
//   --write  step 3 for real: rewrite <audioWork>/<slug>/[en/]<slug>.txt, .src.json and .args.json from the post now
//
// How: md-to-tts-txt.py (standard library only) turns the post as it is now into text in a temp folder, with the
// flags of the last run (<slug>.args.json; without it, fix.tsv when present and --ordinal or not, whichever matches the
// stored .txt better, shown as "guessed"). That text is compared with two things:
//   text   the stored .txt (step 3 is due when they differ)
//   audio  the timing file <audioSync>/<slug>.<lang>.json, which is what the published audio read:
//          exact when it carries "txt" (sha1 of the .txt read, written since 2026-10-23), else by the start of each
//          paragraph's page text (a change after the first 100 characters of a paragraph is missed there).
// Python: $VIENEU_HOME or ~/.vieneu-tts venv, else python3 or python on PATH.
import { existsSync, readFileSync, readdirSync, mkdtempSync, rmSync, copyFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir, homedir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
// The kit's config reader: beside the master skill in the private kit, or inside this skill when it travels alone.
const CONFIG_MJS = [join(HERE, "..", "..", "content", "lib", "config.mjs"), join(HERE, "..", "lib", "config.mjs")].find(existsSync);
if (!CONFIG_MJS) { console.error("stale: no config.mjs found (lib/config.mjs of the skill)"); process.exit(1); }
const { REPO, cfg } = await import(`file://${CONFIG_MJS.replace(/\\/g, "/")}`);
process.chdir(REPO);
const CONVERT = join(HERE, "md-to-tts-txt.py");
const SKILL = relative(REPO, HERE).replace(/\\/g, "/"); // this skill's scripts folder, as the next commands print it
// Folders from content.config.json, so the kit moves between sites.
const CONTENT = { blog: cfg.paths.blog, pages: cfg.paths.pages };
const WORK = cfg.paths.audioWork;
const SYNC = cfg.paths.audioSync;
if (!WORK || !SYNC) { console.error("stale: content.config.json needs paths.audioWork and paths.audioSync"); process.exit(1); }

const args = process.argv.slice(2);
const opt = (k) => args.find((a) => a.startsWith(`--${k}=`))?.split("=")[1];
const flag = (k) => args.includes(`--${k}`);
const only = args.find((a) => !a.startsWith("--"));
const langs = opt("lang") ? [opt("lang")] : ["vi", "en"];
if (langs.some((l) => !["vi", "en"].includes(l))) {
  console.error("usage: stale.mjs [<slug>] [--lang=vi|en] [--write]");
  process.exit(1);
}
if (flag("write") && !only) {
  console.error("stale: --write needs a slug");
  process.exit(1);
}

// The one Python the installer builds, else any Python 3 (the converter needs only the standard library).
const venv = process.env.VIENEU_HOME || join(homedir(), ".vieneu-tts");
const PY = [join(venv, ".venv", "Scripts", "python.exe"), join(venv, ".venv", "bin", "python")].find(existsSync)
  ?? ["python3", "python"].find((p) => spawnSync(p, ["-c", "import sys; assert sys.version_info >= (3, 8)"]).status === 0);
if (!PY) {
  console.error("stale: no Python 3 found (run step 1 of the skill, or put python on PATH)");
  process.exit(1);
}

const read = (f) => readFileSync(f, "utf8").replace(/\r\n/g, "\n");
const paras = (t) => t.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean);
const sha = (t) => createHash("sha1").update(t, "utf8").digest("hex").slice(0, 12);

// Every content file with an audio: line, as { slug, lang, page, md }.
const items = [];
for (const [kind, page] of [["blog", false], ["pages", true]])
  for (const lang of langs) {
    if (!CONTENT[kind]) continue;
    const dir = join(CONTENT[kind], lang);
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir).filter((f) => f.endsWith(".md"))) {
      const slug = f.slice(0, -3);
      if (only && slug !== only) continue;
      const md = join(dir, f);
      const front = read(md).split("\n---", 2)[0];
      if (/^audio:/m.test(front) || only) items.push({ slug, lang, page, md, hasAudio: /^audio:/m.test(front), trust: /^type:\s*["']?Trust/m.test(front) });
    }
  }
if (only && !items.length) {
  console.error(`stale: no ${CONTENT.blog}/<lang>/${only}.md${CONTENT.pages ? ` (or under ${CONTENT.pages})` : ""}`);
  process.exit(1);
}

// Run the converter on the post as it is now; returns { txt, src } read back from the temp folder.
const convert = (it, flags, out) => {
  const r = spawnSync(PY, [CONVERT, it.md.replace(/\\/g, "/"), out, ...flags], {
    encoding: "utf8",
    env: { ...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" },
  });
  if (r.status !== 0) throw new Error(`md-to-tts-txt.py failed on ${it.md}:\n${r.stderr || r.stdout}`);
  return { txt: read(join(out, `${it.slug}.txt`)), src: JSON.parse(read(join(out, `${it.slug}.src.json`))), log: r.stdout.trim() };
};
const toFlags = (a) => [
  ...(a.ordinal ? ["--ordinal"] : []),
  ...(a.read_title ? ["--read-title"] : []),
  ...(a.no_headings ? ["--no-headings"] : []),
  ...(a.skip ?? []).flatMap((s) => ["--skip", s]),
  ...(a.fix ? ["--fix", a.fix] : []),
];
const shellFlags = (f) => f.map((x) => (x.startsWith("--") ? x : `"${x}"`)).join(" ");

// Paragraphs of a that are not in b and the reverse, in order (longest common subsequence).
const diff = (a, b) => {
  const n = a.length, m = b.length, L = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = a[i] === b[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const out = [];
  let i = 0, j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && a[i] === b[j]) { i++; j++; }
    else if (j < m && (i === n || L[i][j + 1] >= L[i + 1][j])) out.push(["+", j + 1, b[j++]]);
    else out.push(["-", i + 1, a[i++]]);
  }
  return out;
};
const changed = (d) => Math.max(d.filter((x) => x[0] === "-").length, d.filter((x) => x[0] === "+").length);

const rows = [];
for (const it of items) {
  const dir = join(WORK, it.slug, ...(it.lang === "en" ? ["en"] : []));
  const stored = join(dir, `${it.slug}.txt`);
  const argsFile = join(dir, `${it.slug}.args.json`);
  const syncFile = join(SYNC, `${it.slug}.${it.lang}.json`);
  const old = existsSync(stored) ? read(stored) : null;
  const tmp = mkdtempSync(join(tmpdir(), "stale-"));
  let flags, guessed = false, now, out = tmp;
  try {
    if (existsSync(argsFile)) {
      flags = toFlags(JSON.parse(read(argsFile)));
      now = convert(it, flags, tmp);
    } else {
      // No record of the last run: fix.tsv when present, and --ordinal or not, whichever is closer to the stored
      // text (a tie goes to the skill's rule: --ordinal for everything but Trust posts).
      guessed = true;
      const fix = join(dir, "fix.tsv");
      const base = existsSync(fix) ? ["--fix", fix.replace(/\\/g, "/")] : [];
      const tries = [["--ordinal", ...base], base].map((f, k) => ({ f, o: join(tmp, String(k)), r: convert(it, f, join(tmp, String(k))) }));
      const score = (t) => (old ? changed(diff(paras(old), paras(t.r.txt))) : 0);
      tries.sort((x, y) => score(x) - score(y) || (it.trust ? 1 : -1) * (x.f[0] === "--ordinal" ? 1 : -1));
      [flags, now, out] = [tries[0].f, tries[0].r, tries[0].o];
    }
  } finally {
    if (!flag("write")) rmSync(tmp, { recursive: true, force: true });
  }

  const textDiff = old ? diff(paras(old), paras(now.txt)) : null;
  let audio = "no audio", audioDiff = null;
  if (it.hasAudio) {
    if (!existsSync(syncFile)) audio = "no timing file";
    else {
      const sync = JSON.parse(read(syncFile));
      audioDiff = diff((sync.segs ?? []).map((s) => s[2]), now.src);
      if (sync.txt) audio = sync.txt === sha(now.txt) ? "ok" : `stale (${changed(audioDiff)} paragraph(s) by start)`;
      else {
        const n = changed(audioDiff);
        // The timing file only holds the start of each paragraph: when those match, the stored .txt is the next witness.
        audio = n ? `stale (${n} paragraph(s))` : old && old !== now.txt ? "likely stale (text changed past paragraph starts)" : "ok";
      }
    }
  }
  const text = old === null ? "no .txt" : textDiff.length ? `${changed(textDiff)} paragraph(s) differ` : "same";
  rows.push({ it, dir, flags, guessed, text, audio, textDiff, audioDiff, now, tmp, out });
}

const STALE = (r) => r.audio !== "ok" || r.text !== "same";
if (!only) {
  console.log("| Slug | Lang | Kind | .txt vs post | Audio vs post | Flags |");
  console.log("|---|---|---|---|---|---|");
  for (const r of rows)
    console.log(`| ${r.it.slug} | ${r.it.lang} | ${r.it.page ? "page" : "post"} | ${r.text} | ${r.audio} | ${shellFlags(r.flags) || "-"}${r.guessed ? " (guessed)" : ""} |`);
  const due = rows.filter(STALE);
  console.log(`\nstale: ${due.length} of ${rows.length} audio to remake.${due.length ? " Details and commands: stale.mjs <slug> --lang=<vi|en>" : ""}`);
  process.exit(0);
}

for (const r of rows) {
  const { it, dir } = r;
  const en = it.lang === "en";
  console.log(`\n## ${it.slug} (${it.lang}, ${it.page ? "page" : "post"})  text: ${r.text}  audio: ${r.audio}`);
  console.log(`flags: ${shellFlags(r.flags) || "(none)"}${r.guessed ? " (guessed: no .args.json yet, check them)" : ""}`);
  const show = (title, d) => {
    if (!d?.length) return;
    console.log(`\n${title}`);
    for (const [s, n, p] of d.slice(0, 40)) console.log(`${s} ${String(n).padStart(3)}  ${p.length > 160 ? p.slice(0, 157) + "..." : p}`);
    if (d.length > 40) console.log(`  ... ${d.length - 40} more`);
  };
  show("Text (- in the stored .txt, + from the post now; number = paragraph):", r.textDiff);
  if (r.audio.includes("stale")) show("Audio (- read by the published audio, + from the post now; start of each paragraph):", r.audioDiff);
  if (flag("write")) {
    for (const f of [`${it.slug}.txt`, `${it.slug}.src.json`, `${it.slug}.sections.json`, `${it.slug}.args.json`]) {
      if (existsSync(join(r.out, f))) copyFileSync(join(r.out, f), join(dir, f));
    }
    console.log(`\nwrote ${join(dir, it.slug)}.txt, .src.json, .sections.json, .args.json (step 3 done). ${r.now.log.split("\n").at(-1)}`);
  }
  if (!STALE(r) && !flag("write")) { console.log("Nothing to remake."); continue; }
  const d = dir.replace(/\\/g, "/");
  const step3 = `"$PY" ${SKILL}/md-to-tts-txt.py ${it.md.replace(/\\/g, "/")} ${d} ${shellFlags(r.flags)}`.trim();
  const voice = cfg.audio.voice ?? "Thiện Minh"; // the site's Vietnamese voice (audio.voice in content.config.json)
  const reader = en ? `"$PY" ${SKILL}/doc-bai-viet-kokoro.py ${d}/${it.slug}.txt` : `"$PY" ${SKILL}/doc-bai-viet-vieneu.py ${d}/${it.slug}.txt --voice "${voice}"`;
  const pub = `node ${SKILL}/publish.mjs ${it.slug}${en ? " --lang=en" : ""}${it.page ? " --page" : ""}`;
  console.log("\nNext:");
  if (!flag("write") && r.text !== "same") console.log(`  3. ${step3}   (or: stale.mjs ${it.slug} --lang=${it.lang} --write), then read the whole .txt`);
  console.log(`  4. ${reader} --sample   (the user listens)`);
  console.log(`  5. ${reader} > <scratchpad>/read-${it.slug}-${it.lang}.log 2>&1   (background)`);
  console.log(`  6. ${pub}`);
}
for (const r of rows) rmSync(r.tmp, { recursive: true, force: true });
