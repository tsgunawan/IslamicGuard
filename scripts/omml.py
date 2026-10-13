"""LaTeX -> native Word equation (OMML) for the subset of LaTeX used in manuscript/draft.md.

latex2mathml turns LaTeX into MathML; this module maps that MathML to OMML, so equations in the
Word file are real equation objects (editable with Word's equation editor), not text or images.
Microsoft's MML2OMML.XSL would do the same but needs an Office installation, which this machine
lacks. Supported: identifiers, numbers, operators, text, sub/superscripts, fractions, accents,
under/over limits, fenced groups and tables (used for piecewise definitions via `cases`).
"""
from __future__ import annotations

import latex2mathml.converter
from lxml import etree

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MML = "{http://www.w3.org/1998/Math/MathML}"


def _el(tag, *children, **attrs):
    e = etree.Element(f"{{{M}}}{tag}", nsmap={"m": M, "w": W})
    for k, v in attrs.items():
        e.set(f"{{{M}}}{k}", v)
    for c in children:
        if c is not None:
            e.append(c)
    return e


def _run(text, plain=False):
    r = _el("r")
    if plain:
        r.append(_el("rPr", _el("nor")))
    t = _el("t"); t.text = text; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    return r


def _wrap(tag, node):
    e = _el(tag)
    for c in _conv(node):
        e.append(c)
    return e


def _table(node):
    rows = node.findall(f"{MML}mtr")
    ncol = max(len(r.findall(f"{MML}mtd")) for r in rows)
    m = _el("m", _el("mPr", _el("mcs", _el("mc", _el("mcPr", _el("count", val=str(ncol)), _el("mcJc", val="left"))))))
    for r in rows:
        mr = _el("mr")
        for cell in r.findall(f"{MML}mtd"):
            mr.append(_wrap("e", cell))
        m.append(mr)
    return m


def _conv(node):
    """Return a list of OMML elements for one MathML node."""
    tag = node.tag.replace(MML, "")
    kids = list(node)
    if tag in ("math", "mrow", "mstyle", "mtd", "mpadded"):
        if len(kids) >= 2 and kids[0].tag == f"{MML}mo" and (kids[0].text or "") == "{" and kids[1].tag == f"{MML}mtable":
            d = _el("d", _el("dPr", _el("begChr", val="{"), _el("endChr", val="")), _el("e", _table(kids[1])))
            return [d] + [x for k in kids[2:] for x in _conv(k)]
        return [x for k in kids for x in _conv(k)]
    if tag in ("mi", "mn", "mo"):
        text = node.text or ""
        upright = tag == "mi" and (node.get("mathvariant") == "normal" or len(text) > 1)  # \mathrm, operator names
        return [_run(text, plain=upright)]
    if tag == "mtext":
        return [_run(node.text or "", plain=True)]
    if tag == "mspace":
        return [_run(" ")]
    if tag == "msub":
        return [_el("sSub", _wrap("e", kids[0]), _wrap("sub", kids[1]))]
    if tag == "msup":
        return [_el("sSup", _wrap("e", kids[0]), _wrap("sup", kids[1]))]
    if tag == "msubsup":
        return [_el("sSubSup", _wrap("e", kids[0]), _wrap("sub", kids[1]), _wrap("sup", kids[2]))]
    if tag == "mfrac":
        return [_el("f", _wrap("num", kids[0]), _wrap("den", kids[1]))]
    if tag == "mover":
        acc = (kids[1].text or "").strip()
        chr_ = {"¯": "̅", "‾": "̅", "^": "̂", "ˆ": "̂", "~": "̃"}.get(acc)
        if chr_:
            return [_el("acc", _el("accPr", _el("chr", val=chr_)), _wrap("e", kids[0]))]
        return [_el("limUpp", _wrap("e", kids[0]), _wrap("lim", kids[1]))]
    if tag == "munder":
        return [_el("limLow", _wrap("e", kids[0]), _wrap("lim", kids[1]))]
    if tag == "munderover":
        return [_el("limUpp", _el("e", _el("limLow", _wrap("e", kids[0]), _wrap("lim", kids[1]))), _wrap("lim", kids[2]))]
    if tag == "mtable":
        return [_table(node)]
    if tag == "mfenced":
        return [_el("d", _wrap("e", node))]
    return [x for k in kids for x in _conv(k)]  # unknown wrapper: keep its content


def omath(latex: str):
    """<m:oMath> element for a LaTeX expression."""
    mml = etree.fromstring(latex2mathml.converter.convert(latex).encode("utf-8"))
    o = _el("oMath")
    for c in _conv(mml):
        o.append(c)
    return o


def omath_para(latex: str):
    return _el("oMathPara", omath(latex))
