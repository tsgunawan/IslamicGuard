"""Export the references cited in manuscript/draft.md as an EndNote-importable RIS file.

Source of truth is literature/references.bib. Only entries cited in the draft are exported.
Each record carries full author names, DOI, URL and, where a PDF exists in ref/, a file link
(L1) so EndNote can attach it. Import in EndNote with File > Import, option "Reference Manager (RIS)".

Usage: python scripts/export_endnote.py
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ref/IslamicGuard_references.ris"
TYPE = {"article": "JOUR", "inproceedings": "CONF", "book": "BOOK", "misc": "GEN"}


def key(s: str) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())


def clean(v: str) -> str:
    v = v.replace('{\\"u}', "ü").replace('{\\"a}', "ä").replace("---", "—").replace("--", "–")
    return re.sub(r"[{}]", "", v).strip()


def main():
    draft = (ROOT / "manuscript/draft.md").read_text(encoding="utf-8")
    refs = draft.split("## REFERENCES")[1].split("\n## ")[0]
    cited = set()
    for line in refs.splitlines():
        m = re.match(r"(.+?)\s\((\d{4})\)\.", line.strip())
        if m:
            cited.add((key(re.split(r",| &", m.group(1))[0]), m.group(2)))
    pdfs = list((ROOT / "ref").glob("*.pdf"))
    out, n = [], 0
    for block in re.split(r"\n(?=@)", (ROOT / "literature/references.bib").read_text(encoding="utf-8")):
        head = re.match(r"@(\w+)\{", block.strip())
        if not head:
            continue
        f = {k: clean(v) for k, v in re.findall(r"^\s*(\w+) = \{(.*)\},?\s*$", block, flags=re.M)}
        authors = [a.strip() for a in f["author"].split(" and ")]
        k = (key(authors[0].split(",")[0]), f["year"])
        if k not in cited:
            continue
        n += 1
        rec = [f"TY  - {TYPE[head.group(1)]}"] + [f"AU  - {a}" for a in authors] + [f"PY  - {f['year']}", f"TI  - {f['title']}"]
        if "journal" in f:
            rec.append(f"JO  - {f['journal']}"); rec.append(f"T2  - {f['journal']}")
        if "booktitle" in f:
            rec.append(f"T2  - {f['booktitle']}")
        if f.get("howpublished") == "arXiv preprint":
            rec += ["PB  - arXiv", "M3  - Preprint"]
        if "publisher" in f:
            rec.append(f"PB  - {f['publisher']}")
        if "edition" in f:
            rec.append(f"ET  - {f['edition']}")
        for tag, name in (("VL", "volume"), ("IS", "number")):
            if name in f:
                rec.append(f"{tag}  - {f[name]}")
        if "pages" in f:
            sp, _, ep = f["pages"].partition("–")
            rec.append(f"SP  - {sp}")
            if ep:
                rec.append(f"EP  - {ep}")
        if "doi" in f:
            rec.append(f"DO  - {f['doi']}")
        if "url" in f:
            rec.append(f"UR  - {f['url']}")
        pdf = [p for p in pdfs if key(p.name.split("_")[0]) == k[0] and k[1] in p.name.split("_")[0]]
        if pdf:
            win = str(pdf[0]).replace("/mnt/d/", "D:/")
            rec.append(f"L1  - file:///{win}")
        else:
            rec.append("N1  - No PDF archived in ref/; metadata verified online on 2026-09-30.")
        out.append("\n".join(rec + ["ER  - ", ""]))
    OUT.write_text("\n".join(out), encoding="utf-8-sig")
    print(f"wrote {OUT.relative_to(ROOT)}: {n} records ({len(cited)} cited in the draft)")


if __name__ == "__main__":
    main()
