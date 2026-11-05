#!/usr/bin/env node
// Step 6 of the audio skill in one command: put the finished audio where the site serves it, check it, wire it in.
//
//   node <skill>/scripts/publish.mjs <slug> [--lang=vi|en] [--page] [--dry] [--keep]
//
//   --lang   vi (default) or en; English reads <audioWork>/<slug>/en/<slug>.m4a
//   --page   the content is <paths.pages>/<lang>/<slug>.md, not a blog post (<paths.blog>)
//   --dry    print what would happen, change nothing
//   --keep   do not delete the local audio after a checked upload
//
// Two stores, chosen by `audio` in content.config.json:
//   R2    { "bucket": "<bucket>", "base": "https://<audio host>" }: `wrangler r2 object put` to <bucket>/<slug>.<lang>.m4a with
//         audio/mp4 and "public, max-age=86400" (replaces the old object under the same key), the section parts to
//         parts/<slug>.<lang>/<hash>.opus cached a year, then `audio.purgeCommand` for that one URL when the site has one
//         (`{url}` in it is replaced), then a HEAD request with a cache-busting query must show the local file's
//         Content-Length. The Cloudflare account comes from the environment, as wrangler reads it.
//   repo  { "dir": "<public folder>", "base": "/audio" }: the audio and its parts are copied into that folder of the site
//         (tracked by git, deployed with it), no upload, no purge, the copy's size is checked instead; base may also be
//         the absolute address the folder is served at. For a site with no R2 (or any object store).
// Folders come from `paths` of content.config.json: audioWork (the working folder of a read), blog and pages (the
// content files), audioSync (the read-along timing files).
// In order: refuses a sample (-thu) or a missing file; the section parts the reader made that the store lacks
// (<slug>.parts.json, parts.py) first, so a failed step changes nothing visitors hear; the joined file; the check; then
// the `audio:` line of the content file is added or replaced (after `cover:` when there is one); the parts no longer
// used are removed from the store; the local audio, its -thu sample and the local parts/ folder are deleted.
import { existsSync, statSync, readFileSync, writeFileSync, unlinkSync, rmSync, readdirSync, mkdirSync, copyFileSync } from "node:fs";
import { execSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// The kit's config reader: beside the master skill in the private kit, or inside this skill when it travels alone.
const HERE = dirname(fileURLToPath(import.meta.url));
const CONFIG_MJS = [join(HERE, "..", "..", "content", "lib", "config.mjs"), join(HERE, "..", "lib", "config.mjs")].find(existsSync);
if (!CONFIG_MJS) { console.error("publish: no config.mjs found (lib/config.mjs of the skill)"); process.exit(1); }
const { REPO, cfg } = await import(`file://${CONFIG_MJS.replace(/\\/g, "/")}`);

process.chdir(REPO);
try { process.loadEnvFile(".env"); } catch {}

const args = process.argv.slice(2);
const opt = (k) => args.find((a) => a.startsWith(`--${k}=`))?.split("=")[1];
const flag = (k) => args.includes(`--${k}`);
const slug = args.find((a) => !a.startsWith("--"));
const lang = opt("lang") ?? "vi";
const dry = flag("dry");
if (!slug || !["vi", "en"].includes(lang)) {
  console.error("usage: publish.mjs <slug> [--lang=vi|en] [--page] [--dry] [--keep]");
  process.exit(1);
}
const fail = (m) => { console.error(`publish: ${m}`); process.exit(1); };

const WORK = cfg.paths.audioWork;
const SYNC = cfg.paths.audioSync;
if (!WORK || !SYNC) fail("content.config.json needs paths.audioWork (the working folder) and paths.audioSync (the timing files)");
const dir = join(WORK, slug, ...(lang === "en" ? ["en"] : []));
const local = join(dir, `${slug}.m4a`);
const sample = join(dir, `${slug}-thu.m4a`);
const contentRoot = flag("page") ? cfg.paths.pages : cfg.paths.blog;
if (!contentRoot) fail(`content.config.json has no paths.${flag("page") ? "pages" : "blog"}`);
const content = join(contentRoot, lang, `${slug}.md`);
const BUCKET = cfg.audio.bucket;
const DIR = cfg.audio.dir; // repo store: a public folder of the site, relative to the repo root
const BASE = cfg.audio.base?.replace(/\/$/, "");
const MODE = DIR ? "repo" : "r2";
const key = `${slug}.${lang}.m4a`;
const url = `${BASE}/${key}`;
if (MODE === "r2" && (!BUCKET || !BASE)) fail("content.config.json needs audio.bucket and audio.base (R2), or audio.dir and audio.base (audio kept in the repo)");
if (MODE === "repo" && !BASE) fail("content.config.json needs audio.base beside audio.dir (the address the folder is served at, for example /audio)");

if (!existsSync(local)) fail(`no ${local} (read the whole post first, step 5; a sample is never published)`);
if (!existsSync(content)) fail(`no ${content}`);
const size = statSync(local).size;
const sync = join(SYNC, `${slug}.${lang}.json`);
console.log(`publish (${MODE}): ${local} (${(size / 1048576).toFixed(1)} MB) -> ${url}`);

const sh = (cmd) => {
  console.log(`  $ ${cmd}`);
  if (!dry) execSync(cmd, { stdio: "inherit", env: process.env });
};
const copy = (from, to) => {
  console.log(`  copy ${from} -> ${to}`);
  if (!dry) { mkdirSync(dirname(to), { recursive: true }); copyFileSync(from, to); }
};
const remove = (f) => { console.log(`  remove ${f}`); if (!dry && existsSync(f)) unlinkSync(f); };

// 0. the section parts (parts.py): store the new ones before the joined file, so a failed step changes nothing
//    visitors hear. A part's name is the hash of its sound, never reused, so it is cached for a year.
const manifestFile = join(dir, `${slug}.parts.json`);
const partsDir = join(dir, "parts");
const manifest = existsSync(manifestFile) ? JSON.parse(readFileSync(manifestFile, "utf8")) : null;
const partKey = (k) => `parts/${slug}.${lang}/${k}.opus`;
let gone = [];
if (manifest) {
  const current = manifest.parts.map((p) => p.key);
  const published = new Set(manifest.published ?? []);
  const fresh = current.filter((k) => !published.has(k));
  gone = [...published].filter((k) => !current.includes(k));
  console.log(`  parts: ${current.length} in the audio, ${fresh.length} to store, ${gone.length} no longer used`);
  for (const k of fresh) {
    const f = join(partsDir, `${k}.opus`);
    if (!existsSync(f)) fail(`part ${f} is missing: read the post again (step 5) before publishing`);
    if (MODE === "r2") sh(`npx wrangler r2 object put "${BUCKET}/${partKey(k)}" --file "${f}" --content-type audio/ogg --cache-control "public, max-age=31536000, immutable" --remote`);
    else copy(f, join(DIR, partKey(k)));
  }
  manifest.published = [...new Set([...published, ...fresh])].sort();
  if (!dry) writeFileSync(manifestFile, JSON.stringify(manifest) + "\n");
} else console.log("  parts: none (no parts.json: audio read before the section parts)");

if (MODE === "r2") {
  // 1. upload (an existing key is overwritten: no -2 names)
  sh(`npx wrangler r2 object put "${BUCKET}/${key}" --file "${local}" --content-type audio/mp4 --cache-control "public, max-age=86400" --remote`);
  // 2. purge that one URL so visitors get the new file now (the site's own command; without one the old file
  //    shows for at most a day, max-age=86400)
  if (cfg.audio.purgeCommand) sh(cfg.audio.purgeCommand.replace("{url}", url));
  else console.log("  no audio.purgeCommand: the edge may serve the old file for up to a day");
  // 3. check what R2 serves, past the edge cache
  if (!dry) {
    const res = await fetch(`${url}?check=${Date.now()}`, { method: "HEAD" });
    const remote = Number(res.headers.get("content-length"));
    if (!res.ok || remote !== size) fail(`R2 answers ${res.status} with ${remote} bytes, local file has ${size}: local audio kept, nothing else changed`);
    console.log(`  checked: ${remote} bytes on R2, same as local`);
  }
} else {
  // 1 to 3. copy into the site's public folder (replaces the old file under the same name) and check the copy
  const served = join(DIR, key);
  copy(local, served);
  if (!dry) {
    const got = statSync(served).size;
    if (got !== size) fail(`${served} has ${got} bytes, local file has ${size}: local audio kept, nothing else changed`);
    console.log(`  checked: ${got} bytes in ${DIR}, same as local`);
  }
}

// 4. the audio: line of the content file
const md = readFileSync(content, "utf8");
const line = `audio: "${url}"`;
const end = md.indexOf("\n---", 3);
let front = md.slice(0, end), rest = md.slice(end);
if (/^audio:.*$/m.test(front)) front = front.replace(/^audio:.*$/m, line);
else if (/^cover:.*$/m.test(front)) front = front.replace(/^(cover:.*)$/m, `$1\n${line}`);
else front += `\n${line}`;
if (front + rest !== md) {
  console.log(`  ${content}: ${line}`);
  if (!dry) writeFileSync(content, front + rest);
} else console.log(`  ${content}: audio line already right`);

// 5. parts the joined file no longer uses: removed from the store only now that the new file is checked
for (const k of gone) {
  if (MODE === "r2") sh(`npx wrangler r2 object delete "${BUCKET}/${partKey(k)}" --remote`);
  else remove(join(DIR, partKey(k)));
}
if (manifest && gone.length) {
  manifest.published = manifest.published.filter((k) => !gone.includes(k));
  if (!dry) writeFileSync(manifestFile, JSON.stringify(manifest) + "\n");
}

// 6. the working copies go: the store holds the audio and its parts (the reader takes a part back from there when it needs it)
if (!flag("keep")) {
  for (const f of [local, sample]) if (existsSync(f)) { console.log(`  delete ${f}`); if (!dry) unlinkSync(f); }
  if (existsSync(partsDir)) {
    console.log(`  delete ${partsDir} (${readdirSync(partsDir).length} file(s), in the ${MODE === "r2" ? "bucket" : DIR} now)`);
    if (!dry) rmSync(partsDir, { recursive: true, force: true });
  }
}

if (!existsSync(sync)) console.log(`warning: no ${sync}: the page will highlight nothing (rerun steps 3 and 5)`);
else if (statSync(sync).mtimeMs < statSync(content).mtimeMs - 864e5) console.log(`warning: ${sync} is older than the post by more than a day: was it written by this read?`);
console.log(`publish: done${dry ? " (dry run)" : ""}. ${MODE === "repo" ? "The audio, its parts and the timing file reach visitors with the next deploy (commit them with the post)." : "The timing file reaches visitors only with the next deploy."}`);
