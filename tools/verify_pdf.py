#!/usr/bin/env python3
"""Structural verification of the generated PDF.

There is no PDF reader in this sandbox, so "it wrote without error" proves
nothing. This parses the file back from bytes and asserts that it is a
well-formed document which a reader will actually open: that the xref offsets
land on their objects, that every page is A4, that every image referenced by a
content stream is declared in that page's resources, that the embedded JPEG
payloads are intact, and that the graphics state is balanced.

Run:  python3 tools/verify_pdf.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "Five-Bedroom-Rental-Comparison-A4.pdf"

A4_W, A4_H = 595.276, 841.890
TOL = 0.5

fails, checks = [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)
    return cond


def main():
    if not PDF.exists():
        print(f"FAIL: {PDF.name} does not exist")
        return 1
    data = PDF.read_bytes()

    # --- header / trailer ---
    ok(data.startswith(b"%PDF-1.4"), "missing %PDF-1.4 header")
    ok(data.rstrip().endswith(b"%%EOF"), "missing %%EOF")

    m = re.search(rb"startxref\s+(\d+)\s*%%EOF\s*$", data)
    if not ok(m is not None, "no startxref found"):
        return report()
    xref_at = int(m.group(1))
    ok(data[xref_at:xref_at + 4] == b"xref",
       f"startxref {xref_at} does not point at an xref table")

    # --- xref table integrity ---
    tail = data[xref_at:]
    hm = re.match(rb"xref\s+0\s+(\d+)\s+", tail)
    if not ok(hm is not None, "malformed xref header"):
        return report()
    count = int(hm.group(1))
    entries = re.findall(rb"(\d{10}) (\d{5}) ([nf])", tail[:hm.end() + 20 * count + 40])
    ok(len(entries) == count,
       f"xref declares {count} entries but {len(entries)} parsed")

    bad_offsets = 0
    for i, (off, _gen, kind) in enumerate(entries):
        if kind != b"n":
            continue
        offset = int(off)
        expect = f"{i} 0 obj".encode()
        if not data[offset:offset + len(expect)] == expect:
            bad_offsets += 1
    ok(bad_offsets == 0,
       f"{bad_offsets} xref offsets do not land on their object header")

    tm = re.search(rb"trailer\s*<<(.+?)>>\s*startxref", data, re.S)
    if not ok(tm is not None, "no trailer dictionary"):
        return report()
    trailer = tm.group(1)
    ok(b"/Root" in trailer, "trailer has no /Root")
    size_m = re.search(rb"/Size\s+(\d+)", trailer)
    ok(size_m is not None and int(size_m.group(1)) == count,
       "trailer /Size disagrees with the xref count")

    root_m = re.search(rb"/Root\s+(\d+) 0 R", trailer)
    root_id = int(root_m.group(1))

    # --- object map ---
    objs = {}
    for om in re.finditer(rb"(\d+) 0 obj\n(.*?)\nendobj\n", data, re.S):
        objs[int(om.group(1))] = om.group(2)
    ok(len(objs) == count - 1,
       f"parsed {len(objs)} objects, xref implies {count - 1}")

    # --- catalog -> pages ---
    cat = objs.get(root_id, b"")
    ok(b"/Type /Catalog" in cat, "/Root is not a /Catalog")
    pm = re.search(rb"/Pages\s+(\d+) 0 R", cat)
    if not ok(pm is not None, "catalog has no /Pages"):
        return report()
    pages_obj = objs.get(int(pm.group(1)), b"")
    ok(b"/Type /Pages" in pages_obj,
       "catalog /Pages does not point at a /Pages node (the off-by-one trap)")

    cm = re.search(rb"/Count\s+(\d+)", pages_obj)
    kids = [int(k) for k in re.findall(rb"(\d+) 0 R", pages_obj)]
    declared = int(cm.group(1)) if cm else -1
    ok(declared == len(kids),
       f"/Pages /Count {declared} != {len(kids)} kids")
    print(f"  pages: {len(kids)}")

    # --- each page ---
    total_img_draws = 0
    for n, kid in enumerate(kids, 1):
        page = objs.get(kid, b"")
        if not ok(b"/Type /Page" in page, f"kid {kid} (page {n}) is not a /Page"):
            continue
        ok(f"/Parent {int(pm.group(1))} 0 R".encode() in page,
           f"page {n} /Parent does not point back at the /Pages node")

        mb = re.search(
            rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", page)
        if ok(mb is not None, f"page {n} has no /MediaBox"):
            w, h = float(mb.group(1)), float(mb.group(2))
            ok(abs(w - A4_W) < TOL and abs(h - A4_H) < TOL,
               f"page {n} is {w:.1f}x{h:.1f}, not A4 {A4_W:.1f}x{A4_H:.1f}")

        # fonts resolve
        for fid in re.findall(rb"/(?:H|HB|HO) (\d+) 0 R", page):
            fo = objs.get(int(fid), b"")
            ok(b"/Type /Font" in fo,
               f"page {n} references object {int(fid)} as a font, but it is not")

        cm2 = re.search(rb"/Contents (\d+) 0 R", page)
        if not ok(cm2 is not None, f"page {n} has no /Contents"):
            continue
        cobj = objs.get(int(cm2.group(1)), b"")
        sm = re.search(rb"<< /Length (\d+) >>\nstream\n(.*)\nendstream",
                       cobj, re.S)
        if not ok(sm is not None, f"page {n} content stream is malformed"):
            continue
        declared_len, stream = int(sm.group(1)), sm.group(2)
        ok(declared_len == len(stream),
           f"page {n} /Length {declared_len} != actual {len(stream)}")
        ok(len(stream) > 0, f"page {n} content stream is empty")

        # Balanced graphics state. Operators must be counted as whole lines,
        # not as substrings: text literals in the stream contain letter pairs
        # that look like operators ("ARITHMETIC" ends in ...ET, and "q"/"Q"
        # occur inside ordinary words), which makes a naive count wrong.
        lines = [l.strip() for l in stream.split(b"\n")]
        n_bt = sum(1 for l in lines if l == b"BT")
        n_et = sum(1 for l in lines if l == b"ET")
        n_q = sum(1 for l in lines if l == b"q")
        n_Q = sum(1 for l in lines if l == b"Q")
        ok(n_bt == n_et, f"page {n} has {n_bt} BT vs {n_et} ET")
        ok(n_q == n_Q, f"page {n} has {n_q} q vs {n_Q} Q "
                       f"(unbalanced graphics state)")

        # every image drawn must be declared in this page's resources
        drawn = set(re.findall(rb"/(Im\d+) Do", stream))
        total_img_draws += len(re.findall(rb"/Im\d+ Do", stream))
        xo = re.search(rb"/XObject << (.+?) >>", page)
        declared_imgs = set(re.findall(rb"/(Im\d+) \d+ 0 R", xo.group(1))) if xo else set()
        missing = drawn - declared_imgs
        ok(not missing,
           f"page {n} draws {[d.decode() for d in missing]} "
           f"but does not declare them in /Resources")

        for iname in drawn:
            im = re.search(rb"/" + iname + rb" (\d+) 0 R", xo.group(1))
            iobj = objs.get(int(im.group(1)), b"")
            ok(b"/Subtype /Image" in iobj,
               f"page {n} {iname.decode()} is not an image XObject")
            ok(b"/DCTDecode" in iobj,
               f"page {n} {iname.decode()} is not DCTDecode")
            jm = re.search(rb"/Length (\d+) >>\nstream\n", iobj)
            if jm:
                start = jm.end()
                payload = iobj[start:start + int(jm.group(1))]
                ok(payload[:2] == b"\xff\xd8",
                   f"page {n} {iname.decode()} payload does not start with JPEG SOI")
                ok(payload[-2:] == b"\xff\xd9",
                   f"page {n} {iname.decode()} payload does not end with JPEG EOI")

    print(f"  image draws: {total_img_draws}")

    # --- images declared once, reused across pages ---
    img_objs = [i for i, b in objs.items() if b"/Subtype /Image" in b]
    print(f"  image XObjects: {len(img_objs)}")
    ok(len(img_objs) <= 14,
       f"{len(img_objs)} image objects for 14 source files - images are being "
       f"duplicated rather than shared")

    # --- layout bounds: nothing may be drawn off the page ---
    # A structurally valid PDF can still be a useless one if content is
    # positioned outside the MediaBox, where no reader will show it.
    worst = []
    for n, kid in enumerate(kids, 1):
        page = objs.get(kid, b"")
        cm2 = re.search(rb"/Contents (\d+) 0 R", page)
        if not cm2:
            continue
        cobj = objs.get(int(cm2.group(1)), b"")
        sm = re.search(rb"stream\n(.*)\nendstream", cobj, re.S)
        if not sm:
            continue
        stream = sm.group(1)

        # text origins, from the text matrix
        ys, xs = [], []
        for tm in re.finditer(rb"1 0 0 1 (-?[\d.]+) (-?[\d.]+) Tm", stream):
            x, y = float(tm.group(1)), float(tm.group(2))
            xs.append(x)
            ys.append(y)
        if ys:
            ok(min(ys) >= -1.0,
               f"page {n}: text baseline at y={min(ys):.1f} is below the page")
            ok(max(ys) <= A4_H + 1.0,
               f"page {n}: text baseline at y={max(ys):.1f} is above the page")
            ok(min(xs) >= -1.0,
               f"page {n}: text at x={min(xs):.1f} is left of the page")
            ok(max(xs) <= A4_W - 4,
               f"page {n}: text origin at x={max(xs):.1f} starts at or past "
               f"the right edge ({A4_W:.0f})")
            worst.append((n, min(ys), max(ys)))

        # rectangles (banding, callouts, cards)
        for rm in re.finditer(
                rb"(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) re", stream):
            x, y, w, h = (float(rm.group(i)) for i in (1, 2, 3, 4))
            ok(y >= -1.0 and y + h <= A4_H + 1.0,
               f"page {n}: rect spans y {y:.1f}..{y + h:.1f}, outside 0..{A4_H:.0f}")
            ok(x >= -1.0 and x + w <= A4_W + 1.0,
               f"page {n}: rect spans x {x:.1f}..{x + w:.1f}, outside 0..{A4_W:.0f}")

        # image placements: the clip rect precedes each /Do
        for im in re.finditer(
                rb"q\n(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) re W n",
                stream):
            x, y, w, h = (float(im.group(i)) for i in (1, 2, 3, 4))
            ok(w > 1 and h > 1,
               f"page {n}: image clip box is degenerate ({w:.1f}x{h:.1f})")
            ok(y >= -1.0 and y + h <= A4_H + 1.0,
               f"page {n}: image clip spans y {y:.1f}..{y + h:.1f}, off-page")
            ok(x >= -1.0 and x + w <= A4_W + 1.0,
               f"page {n}: image clip spans x {x:.1f}..{x + w:.1f}, off-page")

    if worst:
        lo = min(w[1] for w in worst)
        print(f"  lowest text baseline: y={lo:.1f} (page bottom is 0)")

    # --- every text-showing op has a font set before it ---
    for n, kid in enumerate(kids, 1):
        page = objs.get(kid, b"")
        cm2 = re.search(rb"/Contents (\d+) 0 R", page)
        if not cm2:
            continue
        cobj = objs.get(int(cm2.group(1)), b"")
        sm = re.search(rb"stream\n(.*)\nendstream", cobj, re.S)
        if not sm:
            continue
        for block in re.findall(rb"BT\n(.*?)\nET", sm.group(1), re.S):
            if b"Tj" in block:
                ok(b"Tf" in block,
                   f"page {n} shows text in a BT/ET block with no /Tf font set")
                break

    return report()


def report():
    print(f"\n  {checks} checks run")
    if fails:
        print(f"  {len(fails)} FAILED:")
        for f in fails:
            print(f"    - {f}")
        return 1
    print("  all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
