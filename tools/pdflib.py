#!/usr/bin/env python3
"""A minimal, dependency-free A4 PDF writer.

Why this exists: the sandbox has no network for package installs (pip and npm
both fail with a 403 through the proxy) and no browser engine, so neither
reportlab nor the headless-Chromium print path is available. This module writes
PDF 1.4 bytes directly.

What it supports, which is all this report needs:
  - A4 pages, portrait
  - the 14 standard Type1 fonts (no embedding required), with real Helvetica
    metrics so that right-aligned figures in tables line up correctly
  - text, with word-wrap and left/right/centre alignment
  - lines, stroked and filled rectangles
  - baseline JPEG images embedded verbatim via /DCTDecode, optionally
    clipped to a sub-rectangle of the source image so a photo can be cropped
    out of a screenshot without any pixel decoding
"""
from pathlib import Path

A4_W = 595.276
A4_H = 841.890

# Adobe Helvetica / Helvetica-Bold advance widths, units of 1/1000 em,
# for ASCII 32..126. Needed for text measurement.
_HELV = (
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
)
_HELV_B = (
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
    975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
    333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
    611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584,
)

FONTS = {
    "H": ("Helvetica", _HELV),
    "HB": ("Helvetica-Bold", _HELV_B),
    "HO": ("Helvetica-Oblique", _HELV),
}


def text_width(s, font, size):
    """Width of s in points. Unknown glyphs fall back to the width of 'n'."""
    table = FONTS[font][1]
    total = 0
    for ch in s:
        o = ord(ch)
        if 32 <= o <= 126:
            total += table[o - 32]
        else:
            total += table[ord("n") - 32]
    return total * size / 1000.0


def _esc(s):
    """Escape a string for a PDF literal, and fold non-Latin-1 to ASCII."""
    out = []
    for ch in s:
        o = ord(ch)
        if ch in "()\\":
            out.append("\\" + ch)
        elif o < 32:
            out.append(" ")
        elif o <= 126:
            out.append(ch)
        else:
            # The report is written in ASCII; map the few typographic
            # characters that can slip in, and drop anything else.
            out.append({
                "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
                "\u2212": "-", "\u00d7": "x", "\u2192": "->", "\u00b7": ".",
                "\u2264": "<=", "\u2265": ">=", "\u00b0": " deg",
            }.get(ch, ""))
    return "".join(out)


def wrap(s, font, size, width):
    """Greedy word wrap. Over-long single words are hard-split."""
    words = s.split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = cur + " " + w
        if text_width(trial, font, size) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    out = []
    for ln in lines:
        while text_width(ln, font, size) > width and len(ln) > 1:
            lo, hi = 1, len(ln)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if text_width(ln[:mid], font, size) <= width:
                    lo = mid
                else:
                    hi = mid - 1
            out.append(ln[:lo])
            ln = ln[lo:]
        out.append(ln)
    return out


class Image:
    """A baseline JPEG, embedded verbatim with no re-encoding."""

    def __init__(self, path, width, height, components):
        self.path = Path(path)
        self.w = width
        self.h = height
        self.components = components
        self.data = self.path.read_bytes()
        self.name = None  # assigned by the document


class Page:
    def __init__(self, doc):
        self.doc = doc
        self.ops = []
        self.images = {}

    # ---------- graphics ----------

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=0.6):
        if fill is not None:
            self.ops.append(f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        if stroke is not None:
            self.ops.append(f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG")
            self.ops.append(f"{lw:.2f} w")
        op = {(True, True): "B", (True, False): "f", (False, True): "S"}[
            (fill is not None, stroke is not None)
        ]
        self.ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")

    def line(self, x0, y0, x1, y1, color=(0, 0, 0), lw=0.6):
        self.ops.append(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} RG")
        self.ops.append(f"{lw:.2f} w")
        self.ops.append(f"{x0:.2f} {y0:.2f} m {x1:.2f} {y1:.2f} l S")

    # ---------- text ----------

    def text(self, x, y, s, font="H", size=9, color=(0, 0, 0), align="l", width=None):
        s = _esc(s)
        if not s:
            return
        if align in ("r", "c"):
            tw = text_width(s, font, size)
            if align == "r":
                x = x - tw if width is None else x + width - tw
            else:
                x = x - tw / 2 if width is None else x + (width - tw) / 2
        self.ops.append("BT")
        self.ops.append(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg")
        self.ops.append(f"/{font} {size:.2f} Tf")
        self.ops.append(f"1 0 0 1 {x:.2f} {y:.2f} Tm")
        self.ops.append(f"({s}) Tj")
        self.ops.append("ET")

    def para(self, x, y, s, font="H", size=9, leading=None, width=400,
             color=(0, 0, 0), align="l"):
        """Draw wrapped text downward from y. Returns the next free baseline."""
        leading = leading or size * 1.42
        for ln in wrap(s, font, size, width):
            self.text(x, y, ln, font, size, color, align, width if align != "l" else None)
            y -= leading
        return y

    # ---------- images ----------

    def image(self, img, x, y, w, h, crop=None):
        """Place img inside the box (x, y, w, h).

        crop is (fx0, fy0, fx1, fy1) as fractions of the source image with the
        origin at its TOP-LEFT. The visible sub-rectangle is scaled to fill the
        box and everything else is clipped away, which crops a photo out of a
        screenshot without decoding a single pixel.
        """
        if img.name is None:
            img.name = self.doc._register_image(img)
        self.images[img.name] = img

        self.ops.append("q")
        self.ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re W n")

        if crop is None:
            self.ops.append(f"{w:.3f} 0 0 {h:.3f} {x:.3f} {y:.3f} cm")
        else:
            fx0, fy0, fx1, fy1 = crop
            fw, fh = fx1 - fx0, fy1 - fy0
            # Full image drawn at this size makes the crop window exactly fill the box.
            full_w = w / fw
            full_h = h / fh
            # PDF y grows upward; the crop's top edge fy0 sits at the box top.
            ox = x - fx0 * full_w
            oy = y - (1.0 - fy1) * full_h
            self.ops.append(f"{full_w:.3f} 0 0 {full_h:.3f} {ox:.3f} {oy:.3f} cm")

        self.ops.append(f"/{img.name} Do")
        self.ops.append("Q")

    def content(self):
        return "\n".join(self.ops).encode("latin-1", "replace")


class Document:
    def __init__(self):
        self.pages = []
        self._images = {}
        self._img_seq = 0

    def add_page(self):
        p = Page(self)
        self.pages.append(p)
        return p

    def _register_image(self, img):
        key = str(img.path)
        if key in self._images:
            return self._images[key][0]
        self._img_seq += 1
        name = f"Im{self._img_seq}"
        self._images[key] = (name, img)
        return name

    def save(self, path):
        objs = []           # list of bytes bodies, 1-indexed by position

        def add(body):
            objs.append(body)
            return len(objs)

        font_ids = {}
        for key, (base, _) in FONTS.items():
            font_ids[key] = add(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /"
                + base.encode()
                + b" /Encoding /WinAnsiEncoding >>"
            )

        image_ids = {}
        for _, (name, img) in self._images.items():
            cs = b"/DeviceRGB" if img.components == 3 else b"/DeviceGray"
            head = (
                b"<< /Type /XObject /Subtype /Image /Width "
                + str(img.w).encode()
                + b" /Height " + str(img.h).encode()
                + b" /ColorSpace " + cs
                + b" /BitsPerComponent 8 /Filter /DCTDecode /Length "
                + str(len(img.data)).encode() + b" >>\nstream\n"
            )
            image_ids[name] = add(head + img.data + b"\nendstream")

        # Each page consumes two object ids (its content stream, then the page
        # dict), and the /Pages node follows them. Page dicts must reference
        # /Parent before that node is written, so its id is reserved here.
        pages_id = len(objs) + 2 * len(self.pages) + 1
        page_ids = []
        for pg in self.pages:
            data = pg.content()
            cid = add(
                b"<< /Length " + str(len(data)).encode() + b" >>\nstream\n"
                + data + b"\nendstream"
            )
            res_fonts = b" ".join(
                b"/" + k.encode() + b" " + str(font_ids[k]).encode() + b" 0 R"
                for k in FONTS
            )
            if pg.images:
                res_x = b" /XObject << " + b" ".join(
                    b"/" + n.encode() + b" " + str(image_ids[n]).encode() + b" 0 R"
                    for n in pg.images
                ) + b" >>"
            else:
                res_x = b""
            pid = add(
                b"<< /Type /Page /Parent " + str(pages_id).encode()
                + b" 0 R /MediaBox [0 0 "
                + f"{A4_W:.3f} {A4_H:.3f}".encode()
                + b"] /Resources << /Font << " + res_fonts + b" >>" + res_x
                + b" >> /Contents " + str(cid).encode() + b" 0 R >>"
            )
            page_ids.append(pid)

        actual_pages_id = add(
            b"<< /Type /Pages /Count " + str(len(page_ids)).encode()
            + b" /Kids [" + b" ".join(str(i).encode() + b" 0 R" for i in page_ids)
            + b"] >>"
        )
        # Pages object must land on the id the page dicts already point at.
        assert actual_pages_id == pages_id, (actual_pages_id, pages_id)

        root_id = add(b"<< /Type /Catalog /Pages " + str(pages_id).encode() + b" 0 R >>")
        info_id = add(
            b"<< /Title (Five-Bedroom Rental Investment Comparison) "
            b"/Author (Prepared for M Mohsin Chowdhury) "
            b"/Creator (houstoncompare5BRhome/tools/build_report.py) >>"
        )

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += str(i).encode() + b" 0 obj\n" + body + b"\nendobj\n"

        xref_at = len(out)
        out += b"xref\n0 " + str(len(objs) + 1).encode() + b"\n"
        out += b"0000000000 65535 f \n"
        for off in offsets:
            out += f"{off:010d} 00000 n \n".encode()
        out += (
            b"trailer\n<< /Size " + str(len(objs) + 1).encode()
            + b" /Root " + str(root_id).encode() + b" 0 R"
            + b" /Info " + str(info_id).encode() + b" 0 R >>\n"
            b"startxref\n" + str(xref_at).encode() + b"\n%%EOF\n"
        )
        Path(path).write_bytes(out)
        return len(out)
