#!/usr/bin/env python3
"""Turn a blog post (.md) into a clean .txt for the voice reader (doc-bai-viet-vieneu.py). Works for any post.

Usage (PY is the venv python setup.sh builds; any python 3.8+ also works, this file needs only the standard library):
  "$PY" <skill>/scripts/md-to-tts-txt.py <blog>/vi/<slug>.md <audioWork>/<slug>
        [--skip "<H2 text>"] [--read-title] [--no-headings] [--chapters] [--fix <audioWork>/<slug>/fix.tsv]
Writes <out>/<slug>.txt, <slug>.src.json, <slug>.sections.json (paragraphs per part: the opening, each H2, each H3 of an H2 with more than 2; read by the readers' part
cache) and <slug>.args.json (the flags used, read by stale.mjs), or one chapNN.txt
per H2 with --chapters. Only its own output files are overwritten.

What it does: reads the H2 and H3 headings (and deeper) as their own sentences, but drops the post title (read it with
--read-title) and any H1 in the body; --no-headings drops the headings too. It also drops the frontmatter, images, code
blocks (so the prompts posts keep in them), HTML tags and block quote marks; reads "Biết - Tin - Yêu" straight on; keeps the text of links, bold and italics; turns tables into sentences
("first cell. Column: value. ..."), ordered lists into "Bước một: ...", symbols (arrows, parentheses, quotes, dashes,
ampersand) into plain words or commas, drops asides in round brackets, and turns every number into Vietnamese words (2017, 9.999.000 đ, 96%, 2,5, 24/7, 3-5).
--skip drops whole H2 sections (repeatable; normally the closing summary). --fix is a tab-separated file, one
"written<TAB>spoken" pair per line, applied at the end to the spoken text to respell words the voice reads wrong
(brand names). Acronyms are spelled with English letter names (SEO -> "Ét i âu", AI -> "Ây ai"), except the names in
SAID (BTY -> "Biết Tin Yêu") and the capitalised words in CAPS_WORDS; Vietnamese words in capitals are read as words.
After writing it prints a warning for any digit or symbol still left: read the .txt before reading it aloud.

English (--lang en, picked on its own for a file under /en/): the same cleaning, but numbers stay as digits (the English
voice reads them), "3-5" becomes "3 to 5", "24/7" "twenty-four seven", numbered items "Step one" or "First", Vietnamese
names lose their marks (Cường Thạch -> Cuong Thach), and the Vietnamese respellings are off.
"""
import argparse, json, os, re, sys, unicodedata

# Vietnamese on a Windows console (cp1252) raised UnicodeEncodeError on the first log line (2026-11-05, hoanghxn):
# print UTF-8 whatever the console says, so PYTHONUTF8 is no longer a must.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out", nargs="?", help="output folder, usually <audioWork>/<slug> (not needed with --scan)")
ap.add_argument("--scan", action="store_true", help="write nothing: list acronyms, English words, hyphenated words and "
                "numbered lists with how each will be read, to check before reading (user rule 2026-11-05)")
ap.add_argument("--read-title", action="store_true", help="also read the post title aloud (default: left out)")
ap.add_argument("--no-headings", action="store_true", help="leave out the H2, H3 and deeper headings (default: read)")
ap.add_argument("--skip", action="append", default=[], help="drop every H2 section whose heading contains this text (repeatable)")
ap.add_argument("--chapters", action="store_true", help="write one chapNN.txt per H2 instead of one <slug>.txt")
ap.add_argument("--ordinal", action="store_true", help="read numbered items as 'Thứ nhất, Thứ hai' (essays) instead of 'Bước một, Bước hai' (how-to steps)")
ap.add_argument("--fix", help="tab-separated respelling file: written<TAB>spoken")
ap.add_argument("--lang", choices=["vi", "en"], help="language of the post (default: en for a file under /en/, else vi)")
args = ap.parse_args()
if not args.out and not args.scan:
    ap.error("out is required (or use --scan)")
EN = (args.lang or ("en" if "/en/" in args.src.replace("\\", "/") else "vi")) == "en"
# Words the cleaning adds, per language.
W = {"plus": "plus", "or": "or", "and": "and"} if EN else {"plus": "cộng", "or": "hay", "and": "và"}
EN_NUM = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
          "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
EN_ORD = ["", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]

DIG = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

# Acronyms are read with English letter names (user rule 2026-10-22): SEO -> "Ét i âu", AI -> "Ây ai", EC2 -> "I xi 2".
LETTER = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", ["ây", "bi", "xi", "đi", "i", "ép", "di", "ếch", "ai", "giây", "cây", "eo",
              "em", "en", "âu", "pi", "kiu", "a", "ét", "ti", "diu", "vi", "đắp bờ liu", "ích", "oai", "dét"]))
# Capitals that are not spelled: names said in full, acronyms English speakers say as a word, and ordinary words
# written in capitals (button labels, emphasis). A run of capitals holding a Vietnamese letter (THỜI GIAN) is read as
# words on its own. Add here when a post brings a new one.
SAID = {"BTY": "Biết Tin Yêu", "VOTE": "vốt", "RAM": "ram", "AMP": "amp", "DMARC": "đi mác", "CNAME": "xi nêm", "WHOIS": "hu ít",
        "ITIN": "ai tin", "TIN": "tin", "IRIS": "ai rít", "IRSIS": "ai rít", "CNET": "Ci nét", "USD": "Đô la Mỹ"}
SAID_EN = {"BTY": "Know Trust Love", "KTL": "Know Trust Love"}
CAPS_WORDS = set("MUA POST EMAIL NEWSLETTER BULK SEND ADMIN LIVE LINK HOST SHARED CLOUD REGISTER CHECKED DOMAINS VISA "
                 "PAYPAL SPAM WORK AUTO TODAY SMART SMARTS KNOW TRUST LOVE".split())


def acronym(w):
    """One all-caps token: said in full, read as a word, or spelled with English letter names (digits stay digits)."""
    said = SAID_EN if EN else SAID
    if w in said:
        return said[w]
    if w in CAPS_WORDS:
        return w.lower()
    m = re.fullmatch(r"([A-Z]+)(\d*)", w)
    if EN or not m:  # the English voice spells acronyms itself
        return w
    s = " ".join(LETTER[c] for c in m.group(1))
    return s[0].upper() + s[1:] + (f" {m.group(2)}" if m.group(2) else "")


def capitals(t):
    """Runs of all-caps words (2+ letters, joined by single spaces): a run holding a Vietnamese letter (THỜI GIAN,
    CHI PHÍ ẨN) is emphasis and is read as plain words; otherwise each word goes through acronym()."""
    parts = re.split(r"(\w+)", t)  # words at the odd indices
    is_caps = lambda w: len(w) >= 2 and w.isupper()
    i = 1
    while i < len(parts):
        if not is_caps(parts[i]):
            i += 2
            continue
        j = i
        while j + 2 < len(parts) and parts[j + 1] == " " and is_caps(parts[j + 2]):
            j += 2
        words = parts[i : j + 1 : 2]
        vietnamese = any(not w.isascii() for w in words)
        for k, w in zip(range(i, j + 1, 2), words):
            parts[k] = w.lower() if vietnamese else acronym(w)
        i = j + 2
    return "".join(parts)


def three(n, full):
    """Read 0 to 999. full=True for a group that follows a larger one (so 5 is 'không trăm lẻ năm')."""
    h, r = divmod(n, 100)
    t, u = divmod(r, 10)
    out = []
    if h or full:
        out.append(DIG[h] + " trăm")
    if t > 1:
        out.append(DIG[t] + " mươi")
        out.append({1: "mốt", 5: "lăm"}.get(u, DIG[u]) if u else "")
    elif t == 1:
        out.append("mười")
        out.append({5: "lăm"}.get(u, DIG[u]) if u else "")
    elif u:
        if h or full:
            out.append("lẻ")
        out.append(DIG[u])
    return " ".join(x for x in out if x)


def num(n):
    if n == 0:
        return "không"
    units = ["", "nghìn", "triệu", "tỷ"]
    groups = []
    while n:
        n, g = divmod(n, 1000)
        groups.append(g)
    if len(groups) > len(units):  # too large to read as a quantity: say it digit by digit
        return " ".join(DIG[int(c)] for c in str(sum(g * 1000 ** i for i, g in enumerate(groups))))
    out = []
    for i in range(len(groups) - 1, -1, -1):
        if groups[i]:
            out.append((three(groups[i], i < len(groups) - 1) + " " + units[i]).strip())
    return " ".join(out)


def digits(s):
    return " ".join(DIG[int(c)] for c in s)


def numbers(t):
    if EN:  # the English voice reads digits itself; only a range needs a word
        return re.sub(r"(\d)\s*[-–]\s*(\d)", r"\1 to \2", t)
    t = re.sub(r"\$\s?(\d[\d.,]*)", r"\1 đô la", t)
    t = re.sub(r"(\d)\s?(?:đ|₫|vnđ|VND|vnd)\b", r"\1 đồng", t)
    t = re.sub(r"(\d)\s*[-–]\s*(\d)", r"\1 đến \2", t)  # 3-5 -> 3 đến 5
    t = re.sub(r"(\d+)\s*/\s*(\d+)", r"\1 trên \2", t)  # 24/7
    # 9.999.000; a full stop right after ("khoảng 3.500.") ends the sentence (2026-10-22: it was read "ba.năm trăm")
    t = re.sub(r"(?<![\d.])(\d{1,3}(?:\.\d{3})+)(?!\d|\.\d)", lambda m: m.group(1).replace(".", ""), t)
    def dec(m):
        frac = m.group(2)
        spoken = num(int(frac)) if len(frac) <= 2 and not frac.startswith("0") else digits(frac)
        return f"{num(int(m.group(1)))} phẩy {spoken}"
    t = re.sub(r"(\d+),(\d+)", dec, t)  # 2,5
    t = re.sub(r"(\d+)\s*%", lambda m: num(int(m.group(1))) + " phần trăm", t)
    t = re.sub(r"\d+", lambda m: num(int(m.group(0))), t)
    return t


def table(lines):
    """Rows as (page text, spoken text) pairs; the header row is only used for the labels."""
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) or not c for c in r)]
    if len(rows) < 2:
        return [(" ".join(r), " ".join(r)) for r in rows]
    head, out = rows[0], []
    for r in rows[1:]:
        parts = [r[0]] + [f"{h}: {c}" for h, c in zip(head[1:], r[1:]) if c]
        out.append((" ".join(r), ". ".join(p for p in parts if p)))
    return out


def page_text(t):
    """A block as the page shows it (Markdown marks gone, words untouched): the player finds the block by its start
    and the site builds the audio captions (WebVTT) from the whole text."""
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"\[!\w+\]\s*", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[`*~]|(?<!\w)_|_(?!\w)", "", t)
    return re.sub(r"\s+", " ", t).strip()


def dashed_name(m):
    parts = m.group(0).split(" - ")
    return " ".join(parts) if all(p[0].isupper() for p in parts) else m.group(0)


def clean_text(t):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)  # images
    t = re.sub(r"\[!\w+\]\s*", "", t)  # callout marker [!NOTE], [!TIP]: the title after it is kept
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)  # links
    t = re.sub(r"\[([^\]]+)\]", r"\1", t)  # placeholders such as [Loại sản phẩm]
    t = re.sub(r"\bH([1-6])\b", r"heading \1", t)  # H1 -> heading một / heading 1 (user rule 2026-10-22)
    t = re.sub(r"\s\+\s", f" {W['plus']} ", t)
    t = re.sub(r"\b([A-Z])/([A-Z])\b", r"\1 \2", t)  # A/B -> A B
    # A rate: từ/phút -> từ mỗi phút (2026-10-22: it was read "từ hay phút")
    t = re.sub(r"(?<=[^\W\d_])/(?=(?:giây|phút|giờ|tiếng|ngày|tuần|tháng|năm|bài|lần|người|second|minute|hour|day|week|month|year|post)\b)", " per " if EN else " mỗi ", t)
    t = re.sub(r"(?<=[^\W\d_])/(?=[^\W\d_])", f" {W['or']} ", t)  # Trang/Page -> Trang hay Page
    t = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)  # other html
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", t)
    t = re.sub(r"~~([^~]+)~~", r"\1", t)
    t = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️]", "", t)  # emoji
    t = re.sub(r"\s*\([^()]*\)", "", t)  # asides in brackets are not read: "phễu (Phễu nội dung BTY)" (user rule 2026-10-21)
    t = re.sub(r"(?:…|\.\.\.)\s*(?=\w)", lambda m: ", " if t[m.end()].islower() else m.group(0), t)  # "người… sợ viết": a pause
    for a, b in [("→", ", "), ("->", ", "), ("=>", ", "), ("…", "."), ("—", ", "), ("–", ", "), (" & ", f" {W['and']} "), ("&", f" {W['and']} "),
                 ("“", ""), ("”", ""), ('"', ""), ("‘", ""), ("’", "'"), ("(", ", "), (")", ", "), ("[", ", "), ("]", ", ")]:
        t = t.replace(a, b)
    t = capitals(t)
    t = numbers(t)
    # A name written "X - Y - Z" or "X - Y" (Biết - Tin - Yêu, Know - Trust - Love, cặp Biết - Tin) is read straight on,
    # with no pause at the dashes and never "gạch" (user rule 2026-10-22).
    t = re.sub(r"(?<!\w)\w+(?: - \w+)+(?!\w)", dashed_name, t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,;:])(\s*[,;:])+", r"\1", t)  # ", ," -> ","
    t = re.sub(r",\s*\.", ".", t)
    t = re.sub(r"^[,\s]+", "", t)
    return t.strip()


raw = open(args.src, encoding="utf8").read()
title_m = re.search(r'^title:\s*"?(.*?)"?\s*$', raw, re.M)
title = title_m.group(1) if title_m else ""
body = re.sub(r"\A---\n.*?\n---\n", "", raw, count=1, flags=re.S)
body = re.sub(r"^```.*?^```[ \t]*\n?", "", body, flags=re.S | re.M)  # code blocks are not read

# split into sections at H2 (the part before the first H2 is the opening)
parts = re.split(r"^## ", body, flags=re.M)
sections = [("", parts[0])] + [(p.split("\n", 1)[0].strip(), p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]]
sections = [(n, b) for n, b in sections if not any(k in n for k in args.skip)]


def sentence(s):
    """A heading read as its own sentence: keeps a closing ? or !, else ends it with a full stop."""
    s = s.strip().rstrip(".:")
    if not s:
        return s
    s = s[0].upper() + s[1:]
    return s if s[-1] in "?!" else s + "."


def numbered(s):
    """"1. text" or "**1. text**" -> "Bước một: text" (or "Thứ nhất: text" with --ordinal)."""
    m = re.match(r"^(?:\*\*|__)?(\d+)[.)]\s+(.*?)(?:\*\*|__)?$", s)
    if not m:
        return s
    n = int(m.group(1))
    if EN:
        lead = (EN_ORD[n] if n < len(EN_ORD) else f"Number {n}") if args.ordinal else f"Step {EN_NUM[n] if n < len(EN_NUM) else n}"
    else:
        # Vietnamese ordinals: 1 is "nhất" and 4 is "tư" ("Thứ bốn" is wrong); 14, 24... keep "bốn".
        lead = ({1: "Thứ nhất", 4: "Thứ tư"}.get(n, f"Thứ {num(n)}")) if args.ordinal else f"Bước {num(n)}"
    return f"{lead}: {m.group(2)}"


def section_text(name, text):
    """(page text, spoken text) for each block of one H2 section, in reading order."""
    paras = []
    lines = text.split("\n")
    i = 0
    plain = False
    while i < len(lines):
        l = lines[i]
        if l.lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            paras += table(lines[i:j])
            i = j
            continue
        i += 1
        s = l.strip()
        # A list under <!-- not-steps --> is a plain list, not steps: read its items with no "Bước một"
        # (user report 2026-11-01). The flag ends at the first line that is not a list item.
        if s == "<!-- not-steps -->":
            plain = True
            continue
        if s and not re.match(r"\d+[.)]\s", s):
            plain = False
        if not s or re.fullmatch(r"[-*_]{3,}", s) or s.startswith(":::"):
            continue
        if re.match(r"#{1,6}\s", s):  # H3 and deeper are read, an H1 in the body never
            if not args.no_headings and not s.startswith("# "):
                h = re.sub(r"^#{1,6}\s+", "", s)
                paras.append((h, sentence(numbered(h))))
            continue
        s = re.sub(r"^>\s?", "", s)
        s = re.sub(r"^[-*+]\s+(\[[ xX]\]\s+)?", "", s)
        # An ordered list item shows no number in the page text (the list draws it); "**1. text**" keeps it.
        bare = re.sub(r"^\d+[.)]\s+", "", s)
        paras.append((bare, bare if plain else numbered(s)))
    out = [(page_text(a), clean_text(b)) for a, b in paras]
    head = []
    if not args.no_headings and name:
        head = [(page_text(name), sentence(clean_text(numbered(name))))]
    return [(a, b) for a, b in head + out if b]


docs = [section_text(n, b) for n, b in sections]
if args.read_title and title:
    docs[0] = [(page_text(title), sentence(clean_text(title)))] + docs[0]

# Always applied after the --fix pairs (a fix.tsv line for the same words wins). Acronyms are not here: capitals()
# spells them while cleaning (AI -> Ây ai; "ai" and "Ai", the Vietnamese "who", stay as written).
DEFAULT_FIXES = [("24/7", "twenty-four seven")] if EN else []

def read_pairs(path):
    out = []
    for l in open(path, encoding="utf8"):
        if "\t" in l and not l.startswith("#"):
            a, b = l.rstrip("\n").split("\t", 1)
            out.append((a, b))
    return out


def site_dict():
    """The site's own dictionary for this language (audio.dict.<lang> in content.config.json), applied to every post
    after the post's fix.tsv: names and brand words the voice says wrong everywhere (user decision 2026-11-05)."""
    here = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(here, "content.config.json")):
        up = os.path.dirname(here)
        if up == here:
            return []
        here = up
    cfg = json.load(open(os.path.join(here, "content.config.json"), encoding="utf8"))
    rel = ((cfg.get("audio") or {}).get("dict") or {}).get("en" if EN else "vi")
    path = os.path.join(here, rel) if rel else None
    return read_pairs(path) if path and os.path.exists(path) else []


fixes = read_pairs(args.fix) if args.fix else []
fixes += site_dict()
fixes += DEFAULT_FIXES


def respell(t):
    for a, b in fixes:
        t = re.sub(r"(?<!\w)" + re.escape(a) + r"(?!\w)", b, t)
    if EN:  # Vietnamese names lose their marks so the English voice says them plainly: Cường Thạch -> Cuong Thach
        t = unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", t) if not unicodedata.combining(c)))
        t = t.replace("đ", "d").replace("Đ", "D")
    return t


slug = os.path.splitext(os.path.basename(args.src))[0]

# A Vietnamese syllable written without marks (ba, tin, nghe, truong): an ASCII word that is not one is English.
VI_SYLLABLE = re.compile(r"(ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|b|c|d|g|h|k|l|m|n|p|r|s|t|v|x)?[aeiouy]{1,3}(ch|ng|nh|c|m|n|p|t)?")


def scan():
    """--scan: what the reader will meet that a voice may say wrong, each with how it will be read now (after the
    built-in rules and --fix), so the user can decide before the whole post is read (user rule 2026-11-05)."""
    acr, eng, hyph, lists = {}, {}, {}, []

    def note(d, key, spoken, where):
        e = d.setdefault(key, {"n": 0, "spoken": spoken, "where": where})
        e["n"] += 1

    for name, text in sections:
        where = name or "(mở bài)"
        sub = where
        lines = [f"## {name}"] + text.split("\n") if name else text.split("\n")
        i, plain = 0, False
        while i < len(lines):
            raw = lines[i].strip()
            if raw == "<!-- not-steps -->":
                plain = True
                i += 1
                continue
            if re.match(r"#{2,6}\s", raw):
                sub = re.sub(r"^#{2,6}\s+", "", raw)
            # numbered items: one entry per list (or per numbered heading), with how its lead will be read
            m = re.match(r"^(?:#{2,6}\s+)?(?:\*\*|__)?(\d+)[.)]\s+(.*)", raw)
            if m:
                items, heading = [], raw.startswith("#")
                j = i
                while j < len(lines):
                    mm = re.match(r"^(?:#{2,6}\s+)?(?:\*\*|__)?(\d+)[.)]\s+(.*)", lines[j].strip())
                    if not mm:
                        if lines[j].strip() == "" and j + 1 < len(lines) and re.match(r"^(?:\*\*|__)?\d+[.)]\s", lines[j + 1].strip()):
                            j += 1
                            continue
                        break
                    items.append(lines[j].strip())
                    j += 1
                    if heading:
                        break
                first = re.sub(r"^#{2,6}\s+", "", items[0])
                lead = "đọc trơn, không số" if plain and not heading else clean_text(numbered(first)).split(":")[0]
                lists.append({"where": sub, "n": len(items), "first": page_text(first)[:70], "lead": lead,
                              "heading": heading, "plain": plain and not heading})
                if not heading:
                    i = j
                    plain = False
                    continue
            if raw and not re.match(r"\d+[.)]\s", raw):
                plain = False
            # the words as they will reach the voice: no URLs, no asides in brackets (never read)
            t = page_text(re.sub(r"^#{1,6}\s+", "", raw))
            t = re.sub(r"\s*\([^()]*\)", "", t)
            t = re.sub(r"https?://\S+", "", t)
            for w in re.findall(r"\b[A-Z][A-Z0-9]+\b", t):
                if w.isascii() and not re.fullmatch(r"H[1-6]", w):
                    note(acr, w, respell(capitals(w)), sub)
            if not EN:
                for w in re.findall(r"(?<![\w-])[A-Za-z][A-Za-z']+(?![\w-])", t):
                    if w.isupper():
                        continue
                    if not VI_SYLLABLE.fullmatch(w.lower()) or re.search(r"[fjwz]", w.lower()) or re.search(r"[a-z][A-Z]", w):
                        note(eng, w, respell(w), sub)
            for w in re.findall(r"(?<![\w-])\w+(?:-\w+)+(?![\w-])", t):
                note(hyph, w, respell(clean_text(w)), sub)
            for mm in re.finditer(r"(?<!\w)\w+(?: - \w+)+(?!\w)", t):
                note(hyph, mm.group(0), respell(clean_text(mm.group(0))), sub)
            i += 1

    def show(title, d, hint):
        print(f"\n## {title} ({len(d)})")
        if not d:
            print("không có")
            return
        print(hint)
        for k, e in sorted(d.items(), key=lambda kv: (-kv[1]["n"], kv[0].lower())):
            same = " (giọng tự đọc chữ gốc)" if e["spoken"] == k else ""
            print(f"- {k} x{e['n']} -> \"{e['spoken']}\"{same}  [{e['where'][:40]}]")

    print(f"# Quét trước khi đọc: {slug} ({'en' if EN else 'vi'}), cờ: "
          f"{'--ordinal' if args.ordinal else ('Step one' if EN else 'Bước một') + ' (mặc định)'}{', --fix ' + args.fix if args.fix else ''}")
    show("Viết tắt", acr, "Sai thì thêm vào SAID / CAPS_WORDS (mọi bài) hoặc fix.tsv (riêng bài), có user đồng ý.")
    if not EN:
        show("Từ tiếng Anh", eng, "Giọng Việt đọc theo khả năng của nó: đưa từ lạ vào đoạn đọc thử, sai thì fix.tsv.")
    show("Gạch nối", hyph, "Tên 'X - Y' viết hoa đọc liền; số 'a-b' thành khoảng; còn lại giữ nguyên cho giọng tự đọc.")
    print(f"\n## Danh sách đánh số ({len(lists)})")
    if not lists:
        print("không có")
    else:
        print("Bước một = các bước làm theo thứ tự (bài Tin); Thứ nhất = ý hay câu hỏi (--ordinal); "
              "danh sách không phải bước và không cần số: thêm <!-- not-steps --> ngay trên nó.")
        for l in lists:
            kind = "tiêu đề đánh số" if l["heading"] else f"{l['n']} mục"
            print(f"- [{l['where'][:40]}] {kind}, đọc \"{l['lead']}\": {l['first']}")


if args.scan:
    scan()
    sys.exit(0)

os.makedirs(args.out, exist_ok=True)
written = []


def write(name, pairs):
    """<name>.txt to read, and <name>.src.json: the page text of each paragraph, same order, for the readers'
    timing file (the player highlights the block being read)."""
    p = os.path.join(args.out, name + ".txt")
    open(p, "w", encoding="utf8").write(respell("\n\n".join(b for _, b in pairs)) + "\n")
    with open(os.path.join(args.out, name + ".src.json"), "w", encoding="utf8", newline="\n") as f:
        json.dump([a for a, _ in pairs], f, ensure_ascii=False, indent=0)
        f.write("\n")
    written.append(p)


if args.chapters:
    for i, d in enumerate(docs):
        write(f"chap{i:02d}", d)
else:
    write(slug, [pair for d in docs for pair in d])
    # Where each section starts in the .txt, so the readers can keep one audio part per section and read again only
    # the sections whose words changed (parts.py). An H2 with more than 2 H3s is cut further (user decision
    # 2026-11-06): its heading and lead are one part, each H3 one more, so editing one long H3 reads only that H3
    # again; an H2 with 2 H3s stays one part. With --no-headings the H3 headings are not in the text, so the H2
    # stays one part. "h" is the heading as the page shows it ("" for the opening).
    MIN_H3 = 3

    def split_h3(name, body, d):
        subs = [page_text(m.strip()) for m in re.findall(r"^###\s+(.+)$", body, flags=re.M)]
        if len(subs) < MIN_H3:
            return [{"h": page_text(name), "n": len(d)}]
        out, cur, h, k = [], [], page_text(name), 0
        for pair in d:
            if k < len(subs) and pair[0] == subs[k] and cur:
                out.append({"h": h, "n": len(cur)})
                cur, h = [], subs[k]
            if k < len(subs) and pair[0] == subs[k]:
                k += 1
            cur.append(pair)
        if cur:
            out.append({"h": h, "n": len(cur)})
        return out

    secs = [s for (n, b), d in zip(sections, docs) if d for s in split_h3(n, b, d)]
    with open(os.path.join(args.out, slug + ".sections.json"), "w", encoding="utf8", newline="\n") as f:
        json.dump(secs, f, ensure_ascii=False)
        f.write("\n")
    # The flags of this run, so stale.mjs can remake the text the same way later (tracked beside the .txt).
    used = {"ordinal": args.ordinal, "skip": args.skip, "read_title": args.read_title, "no_headings": args.no_headings,
            "fix": args.fix.replace("\\", "/") if args.fix else None}
    with open(os.path.join(args.out, slug + ".args.json"), "w", encoding="utf8", newline="\n") as f:
        json.dump(used, f, ensure_ascii=False)
        f.write("\n")

left = []
for p in written:
    for n, l in enumerate(open(p, encoding="utf8"), 1):
        for m in re.finditer(r"[*|#<>\[\]()_`~=]" if EN else r"[0-9%*|#<>\[\]()_`~=]", l):
            left.append(f"{os.path.basename(p)}:{n}: {l.strip()[max(0, m.start() - 25):m.start() + 25]!r}")
            break
words = sum(len(open(p, encoding="utf8").read().split()) for p in written)
print(f"{len(written)} file(s), {words} words (about {words / 150:.0f} minutes of audio)")
if left:
    print(f"WARNING: {len(left)} line(s) still hold a digit or symbol, fix them in the .txt or add a --fix pair:")
    print("\n".join(left[:20]))
