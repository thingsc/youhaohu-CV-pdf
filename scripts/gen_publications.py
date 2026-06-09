#!/usr/bin/env python3
"""Generate examples/resume/publications.tex from a .bib + a .keys control file.

The .keys file selects which BibTeX entries to render and in what order, grouped
into categories (each becomes a red \\cvsubsectionawesome title with its own
numbered list). This keeps the publication list driven by citekeys: edit the
.bib and/or .keys, re-run, and the .tex is regenerated.

No third-party dependencies; ships a small brace-aware BibTeX parser.
"""

import argparse
import re
import sys

# --- Configuration -----------------------------------------------------------
# Name variants identifying the CV owner; matched entries are highlighted.
MY_NAME = ["Youhao Hu", "Hu, Youhao"]


# --- BibTeX parsing ----------------------------------------------------------
def parse_bib(text):
    """Return {citekey: {field: value}} from BibTeX text (brace-aware)."""
    entries = {}
    i, n = 0, len(text)
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        # entry type
        brace = text.find("{", at)
        if brace == -1:
            break
        # citekey: up to first comma at brace level 0
        j = brace + 1
        while j < n and text[j] not in ",}":
            j += 1
        key = text[brace + 1:j].strip()
        fields = {}
        # parse fields until the matching closing brace of the entry
        while j < n and text[j] != "}":
            j += 1  # skip the comma (or the opening brace position)
            # field name
            eq = text.find("=", j)
            if eq == -1:
                break
            name = text[j:eq].strip().lower()
            if not name:
                j = eq + 1
                continue
            k = eq + 1
            while k < n and text[k] in " \t\r\n":
                k += 1
            if k >= n:
                break
            if text[k] == "{":
                value, k = _read_braced(text, k)
            elif text[k] == '"':
                value, k = _read_quoted(text, k)
            else:
                # bare value up to comma or closing brace
                m = k
                while m < n and text[m] not in ",}":
                    m += 1
                value, k = text[k:m].strip(), m
            fields[name] = " ".join(value.split())
            # advance to next comma or closing brace
            while k < n and text[k] not in ",}":
                k += 1
            j = k
        if key:
            entries[key] = fields
        i = j + 1
    return entries


def _read_braced(text, k):
    """Read a {...} group starting at text[k] == '{'; return (inner, index_after)."""
    depth, start = 0, k
    while k < len(text):
        c = text[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:k], k + 1
        k += 1
    return text[start + 1:], k


def _read_quoted(text, k):
    """Read a "..." string starting at text[k] == '"'; return (inner, index_after)."""
    start = k
    k += 1
    while k < len(text):
        if text[k] == '"':
            return text[start + 1:k], k + 1
        k += 1
    return text[start + 1:], k


# --- Author handling ---------------------------------------------------------
def _normalize(name):
    """Canonical 'first last' lowercase for matching."""
    name = name.strip()
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        name = f"{first} {last}"
    return " ".join(name.lower().split())


MY_KEYS = {_normalize(x) for x in MY_NAME}


def _display_name(name):
    """'Last, First' -> 'First Last'; otherwise unchanged."""
    name = name.strip()
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        return f"{first} {last}"
    return name


def format_authors(raw):
    """Render a BibTeX author field, highlighting the CV owner."""
    names = [a.strip() for a in re.split(r"\s+and\s+", raw) if a.strip()]
    rendered = []
    for nm in names:
        disp = _display_name(nm)
        if _normalize(nm) in MY_KEYS:
            disp = f"\\cvpubme{{{disp}}}"
        rendered.append(disp)
    if len(rendered) <= 1:
        return "".join(rendered)
    return ", ".join(rendered[:-1]) + " and " + rendered[-1]


# --- .keys parsing -----------------------------------------------------------
def parse_keys(text):
    """Return [(category, [citekey, ...]), ...] preserving order."""
    groups = []
    current = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            current = (s[1:-1].strip(), [])
            groups.append(current)
        elif current is not None:
            current[1].append(s)
        # citekeys before any [Category] are ignored
    return groups


# --- Emit --------------------------------------------------------------------
def emit(groups, entries, warn):
    out = [
        "% AUTO-GENERATED by scripts/gen_publications.py -- DO NOT EDIT.",
        "% Edit publications.bib / publications.keys and re-run `make publications`.",
        "",
        "\\cvsection{Publication}",
        "",
    ]
    for category, keys in groups:
        rows = []
        for key in keys:
            e = entries.get(key)
            if e is None:
                warn(f"citekey not found in .bib, skipped: {key}")
                continue
            missing = [f for f in ("title", "author", "doi", "journal") if not e.get(f)]
            if missing:
                warn(f"{key}: missing field(s) {missing}, skipped")
                continue
            rows.append(
                "  \\cvpub\n"
                f"    {{{e['title']}}}\n"
                f"    {{{format_authors(e['author'])}}}\n"
                f"    {{{e['doi']}}}\n"
                f"    {{{e['journal']}}}\n"
                f"    {{{e.get('year', '')}}}"
            )
        if not rows:
            warn(f"category '{category}' has no renderable entries, skipped")
            continue
        out.append(f"\\cvsubsectionawesome{{{category}}}")
        out.append("\\begin{cvpubs}")
        out.append("\n".join(rows))
        out.append("\\end{cvpubs}")
        out.append("")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    base = "examples/resume"
    ap.add_argument("--bib", default=f"{base}/publications.bib")
    ap.add_argument("--keys", default=f"{base}/publications.keys")
    ap.add_argument("--out", default=f"{base}/publications.tex")
    args = ap.parse_args()

    warnings = []

    def warn(msg):
        warnings.append(msg)
        print(f"[gen_publications] WARNING: {msg}", file=sys.stderr)

    try:
        with open(args.bib, encoding="utf-8") as f:
            entries = parse_bib(f.read())
        with open(args.keys, encoding="utf-8") as f:
            groups = parse_keys(f.read())
    except OSError as exc:
        print(f"[gen_publications] ERROR: {exc}", file=sys.stderr)
        return 1

    if not groups:
        print("[gen_publications] ERROR: no categories found in .keys", file=sys.stderr)
        return 1

    content = emit(groups, entries, warn)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)

    n = content.count("\\cvpub\n")
    print(f"[gen_publications] wrote {args.out} ({n} entr{'y' if n == 1 else 'ies'}, "
          f"{len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
