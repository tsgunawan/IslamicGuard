"""Reference integrity audit for manuscript/draft.md (paper.md Section 19).

Checks that can be made offline:
  1. every in-text APA citation has a reference-list entry;
  2. every reference-list entry is cited in the text;
  3. every reference-list entry matches a record in literature/references.bib (first author
     surname + year) and carries that record's DOI/URL;
  4. a PDF for it exists in ref/, or it is reported as metadata-only.
DOI resolution and publisher-metadata comparison need network access and are NOT performed here.

Usage: python scripts/audit_references.py
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "manuscript/draft.md"
OUT = ROOT / "literature/reference_audit.md"


def key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def main() -> int:
    text = DRAFT.read_text(encoding="utf-8")
    body, refs = text.split("## REFERENCES")
    refs = refs.split("\n## ")[0]
    entries = [l.strip() for l in refs.splitlines() if l.strip()]
    ref_keys = {}
    for e in entries:
        m = re.match(r"(.+?)\s\((\d{4})\)\.", e)
        first = re.split(r",| &", m.group(1))[0]
        ref_keys[(key(first), m.group(2))] = e
    cites = set()
    # "(Author, 2025; Author & Other, 2026)" and "Author et al. (2026)" / "Author and Other (2026)"
    for grp in re.findall(r"\(([^()]*\d{4}[^()]*)\)", body):
        for part in grp.split(";"):
            m = re.search(r"([A-Z][\w'’\- ]+?)(?:\s+et al\.|\s*&[^,]+)?,\s*(\d{4})", part.strip())
            if m:
                cites.add((key(m.group(1)), m.group(2)))
    for m in re.finditer(r"([A-Z][\w'’\-]+(?: [A-Z][\w'’\-]+)*?)(?: et al\.| (?:and|&) [A-Z][\w'’\- ]+?)? \((\d{4})\)", body):
        cites.add((key(m.group(1)), m.group(2)))
    # second authors of two-author narrative citations are not separate citations
    seconds = {key(x) for x in re.findall(r"(?:and|&) ([A-Z][\w'’\- ]+?) \(\d{4}\)", body)}
    cites = {c for c in cites if c[0] not in seconds or c in ref_keys}
    cites = {c for c in cites if c[0] not in ("quran", "table", "figure")}

    bib = {}
    for block in (ROOT / "literature/references.bib").read_text(encoding="utf-8").split("\n@")[0:]:
        a = re.search(r"author = \{(.+?)\},\n", block); y = re.search(r"year = \{(\d{4})\}", block)
        if a and y:
            first = re.sub(r"[{}]", "", a.group(1).split(" and ")[0]).split(",")[0]
            d = re.search(r"doi = \{(.+?)\}", block); u = re.search(r"url = \{(.+?)\}", block)
            bib[(key(first), y.group(1))] = (d.group(1) if d else None, u.group(1) if u else None)
    pdfs = [p.name for p in (ROOT / "ref").glob("*.pdf")]

    missing_ref = sorted(c for c in cites if c not in ref_keys)
    uncited = sorted(k for k in ref_keys if k not in cites)
    rows, problems = [], len(missing_ref) + len(uncited)
    for k, e in sorted(ref_keys.items()):
        in_bib = k in bib
        link_ok = in_bib and any(x and x in e for x in bib[k])
        pdf = any(key(p.split("_")[0]) == k[0] and k[1] in p.split("_")[0] for p in pdfs)
        problems += (not in_bib) + (not link_ok)
        rows.append(f"| {e[:60]}… | {'yes' if in_bib else 'NO'} | {'yes' if link_ok else 'NO'} | {'yes' if pdf else 'no PDF in ref/'} |")
    unused = sorted(k for k in bib if k not in ref_keys)
    md = ["# Reference audit — manuscript/draft.md", "",
          f"- In-text citations found: {len(cites)}; reference-list entries: {len(ref_keys)}.",
          f"- Cited in text but missing from the reference list: {missing_ref or 'none'}.",
          f"- In the reference list but not cited: {uncited or 'none'}.",
          f"- In literature/references.bib but not used in the draft: {[f'{a}{y}' for a, y in unused] or 'none'}.",
          "- Not checked (needs network): DOI resolution and comparison with publisher metadata.", "",
          "| Reference | In references.bib | DOI/URL matches bib | PDF archived |", "|---|---|---|---|"] + rows
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:7])); print("problems:", problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
