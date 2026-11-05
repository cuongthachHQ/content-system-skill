// Content kit: the one reader of content.config.json (rule .agents/rules/08-content-kit.md).
// Every script of a content skill imports this instead of hard-coding a folder of the site, a store or the site
// name. Offline, no dependencies.
//
//   import { REPO, cfg, p } from "../../content/lib/config.mjs";   // from .agents/skills/<skill>/scripts/
//   cfg.site.domain            -> the site's domain
//   p("blog", "vi")            -> "<repo>/<paths.blog>/vi" (absolute)
//   p("docs.en")               -> "<repo>/<paths.docs.en>"
//
// The repo root is the nearest ancestor folder holding content.config.json (so the file works from the
// .agents copy, the .claude mirror, and later from a kit installed by `npx skills add`).
import { readFileSync, existsSync } from "node:fs";
import { dirname, join, resolve, isAbsolute } from "node:path";
import { fileURLToPath } from "node:url";

export const CONFIG_FILE = "content.config.json";

export function findRepo(from = dirname(fileURLToPath(import.meta.url))) {
  let dir = resolve(from);
  for (;;) {
    if (existsSync(join(dir, CONFIG_FILE))) return dir;
    const up = dirname(dir);
    if (up === dir) throw new Error(`content kit: no ${CONFIG_FILE} above ${from}`);
    dir = up;
  }
}

export const REPO = process.env.CONTENT_KIT_REPO ? resolve(process.env.CONTENT_KIT_REPO) : findRepo();

const DEFAULTS = {
  kit: "content-kit",
  site: { name: "", domain: "", defaultLang: "vi", langs: ["vi", "en"] },
  paths: {},
  audio: {},
};

function load() {
  const raw = JSON.parse(readFileSync(join(REPO, CONFIG_FILE), "utf8"));
  const out = { ...DEFAULTS, ...raw, site: { ...DEFAULTS.site, ...raw.site }, paths: { ...raw.paths }, audio: { ...raw.audio } };
  // Only the blog folder is required: a repo that holds one skill of the kit (the audio tool of a WordPress site)
  // has no recordings or brand profile, and p() names any other missing path when a skill asks for it.
  if (!out.paths.blog) throw new Error(`content kit: ${CONFIG_FILE} lacks paths.blog`);
  return out;
}

export const cfg = load();

/** Absolute path of a configured folder or file. `key` may be dotted ("docs.en"); extra parts are joined. */
export function p(key, ...parts) {
  const v = key.split(".").reduce((o, k) => (o == null ? undefined : o[k]), cfg.paths);
  if (typeof v !== "string") throw new Error(`content kit: no path "${key}" in ${CONFIG_FILE}`);
  return isAbsolute(v) ? join(v, ...parts) : join(REPO, v, ...parts);
}

/** Folder of one language of the blog, or of the docs. */
export const blogDir = (lang = cfg.site.defaultLang) => p("blog", lang);
export const docsDir = (lang = "en") => p(`docs.${lang}`);

/** True when a URL points at this site (absolute or root-relative). */
export function isSiteUrl(href) {
  if (!href) return false;
  if (href.startsWith("/")) return true;
  const d = cfg.site.domain.replace(/\./g, "\\.");
  return new RegExp(`^https?://(www\\.)?${d}(/|$)`).test(href);
}

/** Strip the site origin from a URL, keeping the path (for link checks). */
export function sitePath(href) {
  const d = cfg.site.domain.replace(/\./g, "\\.");
  return href.replace(new RegExp(`^https?://(www\\.)?${d}`), "").split(/[#?]/)[0];
}
