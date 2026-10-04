#!/usr/bin/env python3
"""Build the A4 PDF comparison report.

Run:  python3 tools/model.py && python3 tools/build_report.py
Out:  Five-Bedroom-Rental-Comparison-A4.pdf
"""
import json
from pathlib import Path

import pdflib as P
from jpeginfo import jpeg_info

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
ASSETS = ROOT / "assets" / "elevations"
OUT = ROOT / "Five-Bedroom-Rental-Comparison-A4.pdf"

# ---- palette ----
INK = (0.12, 0.12, 0.14)
MUTED = (0.42, 0.42, 0.46)
RULE = (0.78, 0.78, 0.80)
BAND = (0.945, 0.945, 0.955)
RED = (0.70, 0.12, 0.12)
REDBG = (0.985, 0.93, 0.93)
AMBER = (0.62, 0.42, 0.04)
AMBERBG = (0.995, 0.96, 0.88)
GREEN = (0.10, 0.42, 0.22)
WHITE = (1, 1, 1)

M = 44.0                      # page margin
CW = P.A4_W - 2 * M           # content width

# Visible photo region inside each WhatsApp screenshot, as fractions of the
# source image from its top-left. Estimated by eye from the rendered images -
# the sandbox has no image library to measure with - and deliberately set a
# little generous, so a sliver of chat chrome may show rather than risk
# slicing a roofline or garage off the elevation.
CROPS = {
    "IMG_3489.jpeg": (0.205, 0.035, 0.962, 0.640),
    "IMG_3490.jpeg": (0.205, 0.015, 0.962, 0.608),
    "IMG_3491.jpeg": (0.205, 0.015, 0.962, 0.608),
    "IMG_3492.jpeg": (0.205, 0.015, 0.960, 0.580),
    "IMG_3493.jpeg": (0.205, 0.015, 0.962, 0.628),
    "IMG_3494.jpeg": (0.205, 0.015, 0.962, 0.628),
    "IMG_3496.jpeg": (0.020, 0.010, 0.995, 0.558),
    "IMG_3499.jpeg": (0.090, 0.010, 0.930, 0.575),
    "IMG_3501.jpeg": (0.030, 0.015, 0.950, 0.625),
    "IMG_3502.jpeg": (0.205, 0.015, 0.962, 0.560),
    "IMG_3503.jpeg": (0.050, 0.010, 0.980, 0.605),
    "IMG_3504.jpeg": (0.060, 0.010, 0.935, 0.575),
    "IMG_3505.jpeg": (0.020, 0.015, 0.975, 0.575),
    "IMG_3506.jpeg": (0.000, 0.000, 1.000, 1.000),
}

_imgcache = {}


def img(name):
    if name not in _imgcache:
        info = jpeg_info(ASSETS / name)
        _imgcache[name] = P.Image(ASSETS / name, info["width"], info["height"],
                                  info["components"])
    return _imgcache[name]


def money(v):
    if v is None:
        return "n/a"
    return ("-$" if v < 0 else "$") + f"{abs(int(round(v))):,}"


def pct(v, dp=2):
    return "n/a" if v is None else f"{v * 100:.{dp}f}%"


class Report:
    def __init__(self):
        self.doc = P.Document()
        self.pg = None
        self.y = 0
        self.pageno = 0
        self.toc = []

    # ---- page frame ----

    def new_page(self, title=None, kicker=None):
        self.pg = self.doc.add_page()
        self.pageno += 1
        self.y = P.A4_H - M

        if self.pageno > 1:
            self.pg.text(M, P.A4_H - 26,
                         "Five-Bedroom Rental Investment Comparison",
                         "H", 7.2, MUTED)
            self.pg.text(M, P.A4_H - 26, f"{self.pageno}", "H", 7.2, MUTED,
                         align="r", width=CW)
            self.pg.line(M, P.A4_H - 32, M + CW, P.A4_H - 32, RULE, 0.5)
            self.y = P.A4_H - 52

        self.pg.text(M, 28, "Prepared 4 October 2026  -  figures are indicative, "
                            "not quotes  -  see 'What is not verified'",
                     "H", 6.6, MUTED)
        self.pg.text(M, 28, "houstoncompare5BRhome", "H", 6.6, MUTED,
                     align="r", width=CW)

        if kicker:
            self.pg.text(M, self.y, kicker.upper(), "HB", 7.6, MUTED)
            self.y -= 13
        if title:
            self.pg.text(M, self.y, title, "HB", 15.5, INK)
            self.y -= 8
            self.pg.line(M, self.y, M + CW, self.y, INK, 1.1)
            self.y -= 17
            self.toc.append((title, self.pageno))
        return self.pg

    def space(self, n=10):
        self.y -= n

    def need(self, h, title=None, kicker=None):
        if self.y - h < 54:
            self.new_page(title, kicker)
            return True
        return False

    # ---- blocks ----

    def h2(self, s, size=10.4):
        self.need(34)
        self.pg.text(M, self.y, s, "HB", size, INK)
        self.y -= size * 1.35

    def body(self, s, size=8.7, color=INK, width=None, indent=0.0, leading=None):
        width = width or (CW - indent)
        lines = P.wrap(s, "H", size, width)
        leading = leading or size * 1.46
        for ln in lines:
            if self.y < 56:
                self.new_page()
            self.pg.text(M + indent, self.y, ln, "H", size, color)
            self.y -= leading
        return self.y

    def bullets(self, items, size=8.7, color=INK, bullet="-"):
        for it in items:
            lines = P.wrap(it, "H", size, CW - 14)
            for i, ln in enumerate(lines):
                if self.y < 56:
                    self.new_page()
                if i == 0:
                    self.pg.text(M + 2, self.y, bullet, "H", size, MUTED)
                self.pg.text(M + 14, self.y, ln, "H", size, color)
                self.y -= size * 1.44
            self.y -= 2.2

    def callout(self, title, text, tone="red"):
        fg, bg = (RED, REDBG) if tone == "red" else (AMBER, AMBERBG)
        size = 8.6
        tl = P.wrap(title, "HB", 9.4, CW - 24)
        bl = P.wrap(text, "H", size, CW - 24)
        h = 15 + len(tl) * 13 + len(bl) * size * 1.46
        self.need(h + 12)
        top = self.y + 4
        self.pg.rect(M, top - h, CW, h, fill=bg)
        self.pg.rect(M, top - h, 3.2, h, fill=fg)
        yy = top - 14
        for ln in tl:
            self.pg.text(M + 13, yy, ln, "HB", 9.4, fg)
            yy -= 13
        for ln in bl:
            self.pg.text(M + 13, yy, ln, "H", size, INK)
            yy -= size * 1.46
        self.y = top - h - 12

    def table(self, cols, rows, size=7.9, head_size=7.4, row_h=None,
              zebra=True, head_fill=None):
        """cols: list of (label, width, align). rows: list of list of str."""
        row_h = row_h or size * 1.72
        total = sum(c[1] for c in cols)
        sx = M + (CW - total) / 2 if total < CW else M

        self.need(row_h * 2 + 18)
        hy = self.y
        self.pg.rect(sx, hy - row_h + 4, total, row_h, fill=head_fill or (0.90, 0.90, 0.92))
        x = sx
        for label, w, al in cols:
            self.pg.text(x + 4 if al == "l" else x, hy - row_h + 10,
                         label, "HB", head_size, INK,
                         align=al, width=(w - 8) if al != "l" else None)
            x += w
        self.y = hy - row_h + 4
        self.pg.line(sx, self.y, sx + total, self.y, INK, 0.7)

        for ri, r in enumerate(rows):
            if self.y - row_h < 54:
                self.new_page()
                hy = self.y
                self.pg.rect(sx, hy - row_h + 4, total, row_h,
                             fill=head_fill or (0.90, 0.90, 0.92))
                x = sx
                for label, w, al in cols:
                    self.pg.text(x + 4 if al == "l" else x, hy - row_h + 10,
                                 label, "HB", head_size, INK,
                                 align=al, width=(w - 8) if al != "l" else None)
                    x += w
                self.y = hy - row_h + 4
                self.pg.line(sx, self.y, sx + total, self.y, INK, 0.7)

            if zebra and ri % 2 == 1:
                self.pg.rect(sx, self.y - row_h, total, row_h, fill=BAND)
            x = sx
            for (label, w, al), cell in zip(cols, r):
                txt = str(cell)
                col = INK
                fnt = "H"
                if txt.startswith("!"):
                    txt, col, fnt = txt[1:], RED, "HB"
                elif txt.startswith("*"):
                    txt, fnt = txt[1:], "HB"
                elif txt.startswith("~"):
                    txt, col = txt[1:], MUTED
                while P.text_width(txt, fnt, size) > w - 8 and len(txt) > 2:
                    txt = txt[:-1]
                self.pg.text(x + 4 if al == "l" else x, self.y - row_h + 6.4,
                             txt, fnt, size, col,
                             align=al, width=(w - 8) if al != "l" else None)
                x += w
            self.y -= row_h
        self.pg.line(sx, self.y, sx + total, self.y, RULE, 0.6)
        self.y -= 11


# ======================================================================

def build():
    res = json.loads((D / "results.json").read_text())
    props = json.loads((D / "properties.json").read_text())
    A = json.loads((D / "assumptions.json").read_text())
    by_id = {r["id"]: r for r in res["rows"]}
    ranked = [by_id[i] for i in res["ranked_ids"]]
    unrank = [by_id[i] for i in res["unrankable_ids"]]
    excl = [by_id[i] for i in res["excluded_ids"]]
    priced = ranked

    R = Report()

    # ---------------- page 1: cover + verdict ----------------
    pg = R.new_page()
    pg.rect(M, P.A4_H - 190, CW, 146, fill=(0.10, 0.13, 0.20))
    pg.text(M + 22, P.A4_H - 84, "FIVE-BEDROOM RENTAL", "HB", 23, WHITE)
    pg.text(M + 22, P.A4_H - 110, "INVESTMENT COMPARISON", "HB", 23, WHITE)
    pg.text(M + 22, P.A4_H - 136, "12 properties across Texas and Louisiana, "
                                  "scored for long-term buy-and-hold",
            "H", 9.6, (0.80, 0.83, 0.90))
    pg.text(M + 22, P.A4_H - 162, "Prepared for M Mohsin Chowdhury  -  "
                                  "4 October 2026", "H", 8.4, (0.66, 0.70, 0.80))
    pg.text(M + 22, P.A4_H - 176, "Source: 14 listing screenshots in "
                                  "MMS-ITS/Houstonhome", "H", 7.6,
            (0.58, 0.62, 0.74))
    R.y = P.A4_H - 206

    R.h2("The finding that governs everything else", 12)
    R.body(
        "At today's investor mortgage rates, none of the five properties with a "
        "confirmed price generates positive cash flow, and none comes close. "
        "This is not a matter of picking the best one. Every one of them loses "
        "money every month, and the losses are large.",
        9.3)
    R.space(4)

    worst = min(priced, key=lambda r: r["cf_base"])
    best = max(priced, key=lambda r: r["cf_base"])
    R.callout(
        "Negative leverage, on every property",
        f"The five priced homes return capitalisation rates of "
        f"{min(r['cap_rate'] for r in priced) * 100:.1f}% to "
        f"{max(r['cap_rate'] for r in priced) * 100:.1f}%, while the debt to buy "
        f"them costs about {A['financing']['rate_base'] * 100:.2f}%. You would be "
        f"borrowing at roughly three to five times the rate the asset earns. "
        f"Monthly cash flow runs from {money(best['cf_base'])} on the best to "
        f"{money(worst['cf_base'])} on the worst - that is "
        f"{money(best['cf_base_year'])} to {money(worst['cf_base_year'])} a year "
        f"out of your pocket, before a single repair. Debt service coverage lands "
        f"between {min(r['dscr'] for r in priced):.2f} and "
        f"{max(r['dscr'] for r in priced):.2f}, against the 1.20-1.25 a lender "
        f"looks for on a rental.")

    R.h2("Ranked, with the caveat that the ranking is relative", 11)
    R.body("Scores are out of 10 across 18 weighted criteria. These are "
           "rankings among loss-making options, not endorsements.", 8.6, MUTED)
    R.space(3)
    R.table(
        [("#", 22, "c"), ("Property", 150, "l"), ("Builder", 96, "l"),
         ("Price", 58, "r"), ("Bed", 26, "c"), ("Cap", 42, "r"),
         ("Cash flow/mo", 66, "r"), ("DSCR", 34, "r"), ("Score", 36, "r")],
        [[str(r["rank"]),
          r["label"].split(" (")[0],
          r["builder"].split(" (")[0][:22],
          money(r["price"]),
          str(r["beds"] or "?"),
          pct(r["cap_rate"], 2),
          "!" + money(r["cf_base"]),
          f"{r['dscr']:.2f}",
          "*" + f"{r['score']:.2f}"] for r in ranked],
        size=7.8)

    R.body("Seven more properties could not be ranked because no price was "
           "obtainable, and one screenshot could not be identified at all. "
           "Both groups are set out later in full.", 8.4, MUTED)

    # ---------------- page 2: the arithmetic ----------------
    R.new_page("Why every one of them loses money", "the central arithmetic")

    R.body(
        "The mechanism is the same in each case, so it is worth following once "
        "in full. Taking the best-scoring property, the Starlight Homes Pioneer "
        "at 5646 Shelford Birch Drive in Cut and Shoot - the one price in this "
        "set confirmed directly on the builder's own website:", 9)
    R.space(6)

    p6 = by_id["P06"]
    lines = [
        ("Asking price (builder-direct)", money(p6["price"])),
        (f"Deposit at {A['financing']['down_payment_pct'] * 100:.0f}%", money(p6["down"])),
        ("Loan amount", money(p6["loan"])),
        (f"Monthly principal and interest at {A['financing']['rate_base'] * 100:.2f}%",
         money(p6["pi_base"])),
        (f"Property tax at {p6['tax_rate'] * 100:.1f}% of price (Montgomery Co. with MUD)",
         money(p6["tax_month"])),
        ("Insurance (Houston metro, hurricane-exposed)", money(p6["ins_month"])),
        ("HOA", money(p6["hoa_month"])),
    ]
    for lab, val in lines:
        R.pg.text(M + 10, R.y, lab, "H", 8.7, INK)
        R.pg.text(M, R.y, val, "H", 8.7, INK, align="r", width=CW - 10)
        R.y -= 13.4
    R.pg.line(M + 10, R.y + 4, M + CW - 10, R.y + 4, INK, 0.7)
    R.y -= 6
    fixed = p6["pi_base"] + p6["tax_month"] + p6["ins_month"] + p6["hoa_month"]
    R.pg.text(M + 10, R.y, "Total fixed monthly outgoings", "HB", 8.9, INK)
    R.pg.text(M, R.y, money(fixed), "HB", 8.9, INK, align="r", width=CW - 10)
    R.y -= 20

    R.body(
        f"Against that, the rent. The published median rent for ZIP 77303 is "
        f"{money(p6['rent_median'] if p6.get('rent_median') else 1800)} a month. "
        f"This house is larger than the median rental unit, so the model lifts "
        f"that by {(A['rent_size_premium']['factor'] - 1) * 100:.0f}% to "
        f"{money(p6['rent'])}. From that gross figure come vacancy at "
        f"{A['operating']['vacancy_pct'] * 100:.0f}%, maintenance and capital "
        f"reserve at {A['operating']['maintenance_capex_pct'] * 100:.0f}%, and "
        f"management at {A['operating']['management_pct'] * 100:.0f}% - together "
        f"{p6['leak_pct'] * 100:.0f}% - leaving {money(p6['egi_month'])} actually "
        f"collected.", 9)
    R.space(4)

    R.callout(
        f"{money(p6['egi_month'])} collected against {money(fixed)} owed",
        f"That is {money(p6['cf_base'])} a month, or "
        f"{money(p6['cf_base_year'])} a year, on the BEST property in the set. "
        f"To break even the house would have to rent for "
        f"{money(p6['breakeven_rent'])} a month - about "
        f"{(p6['breakeven_rent'] / p6['rent'] - 1) * 100:.0f}% above what the "
        f"market supports. The 1% rule of thumb would want "
        f"{money(p6['one_pct_rent_needed'])}; the market gives "
        f"{money(p6['rent'])}, which is "
        f"{p6['one_pct_ratio'] * 100:.2f}% of price.")

    R.h2("The same test applied to all five priced properties", 10.6)
    R.table(
        [("Property", 132, "l"), ("Price", 54, "r"), ("Rent", 46, "r"),
         ("Break-even rent", 72, "r"), ("Shortfall", 54, "r"),
         ("1% rule needs", 66, "r"), ("Actual", 44, "r")],
        [[r["label"].split(" (")[0], money(r["price"]), money(r["rent"]),
          money(r["breakeven_rent"]),
          "!" + money(r["rent"] - r["breakeven_rent"]),
          money(r["one_pct_rent_needed"]),
          f"{r['one_pct_ratio'] * 100:.2f}%"] for r in priced],
        size=7.8)

    R.body(
        "Not one property reaches even two-thirds of the rent it would need to "
        "cover its own costs. The gap is structural, not a matter of shopping "
        "harder: it is the product of a 7.5-8.5% cost of money meeting a 1.5-3% "
        "earning yield.", 8.8)
    R.space(6)

    R.h2("Sensitivity: does a better rate rescue it?", 10.6)
    R.body(f"Monthly cash flow at {A['financing']['rate_low'] * 100:.2f}%, "
           f"{A['financing']['rate_base'] * 100:.2f}% and "
           f"{A['financing']['rate_high'] * 100:.2f}%.", 8.5, MUTED)
    R.space(3)
    R.table(
        [("Property", 150, "l"), ("at 7.75%", 74, "r"), ("at 8.25%", 74, "r"),
         ("at 8.75%", 74, "r"), ("Swing", 64, "r")],
        [[r["label"].split(" (")[0],
          "!" + money(r["cf_low"]), "!" + money(r["cf_base"]),
          "!" + money(r["cf_high"]),
          money(r["cf_low"] - r["cf_high"])] for r in priced],
        size=7.9)
    R.body(
        "A full percentage point off the rate moves cash flow by roughly $140-190 "
        "a month. The shortfall is $890-1,580. Rate shopping, a builder buydown, "
        "even a return to 6% lending does not close a gap of that size - the "
        "deficit is too large by a factor of five or more.", 8.8)

    # ---------------- page 3: method ----------------
    R.new_page("Method, and what the numbers rest on", "how to read this")

    R.h2("Where the property data came from", 10.4)
    R.body(
        "You supplied 14 WhatsApp screenshots in the MMS-ITS/Houstonhome "
        "repository, each pairing a frontal elevation with a Zillow share link. "
        "Those links are the entire factual basis for the property identities. "
        "Zillow, Redfin, Realtor, Trulia, Lennar and NewHomeSource all refuse "
        "automated page requests from this environment - every direct fetch "
        "returned HTTP 403 - so each property was instead identified through "
        "web search, and every figure carries its own provenance in "
        "data/properties.json.", 8.8)
    R.space(5)

    R.h2("Price confidence is not uniform, and that matters", 10.4)
    rec = props["inventory_reconciliation"]
    R.table(
        [("Confidence", 112, "l"), ("Count", 38, "c"), ("What it means", 310, "l")],
        [["Confirmed", str(rec["with_confirmed_exact_price"]),
          "An exact list price appeared verbatim in a source"],
         ["Derived", str(rec["with_derived_price"]),
          "Computed from $/sqft x sqft - arithmetic, not a quoted price"],
         ["Range only", str(rec["with_range_only"]),
          "Only a community or plan-level range was published"],
         ["None", str(rec["with_no_price"]),
          "No price located anywhere"]],
        size=8)
    R.body(
        "Only Angleton, Dayton, Crosby and Cut and Shoot have prices quoted "
        "verbatim by a source. Caldwell's $277,750 is arithmetic - Redfin's "
        "$101/sqft multiplied by Lennar's published 2,750 sqft - and is shown "
        "throughout as derived rather than quoted. The remaining seven have no "
        "usable price, which is why the emails in this pack lead with that "
        "question.", 8.8)
    R.space(5)

    R.h2("The financing and operating assumptions", 10.4)
    f = A["financing"]
    o = A["operating"]
    R.table(
        [("Input", 150, "l"), ("Value", 62, "r"), ("Basis", 248, "l")],
        [["Deposit", f"{f['down_payment_pct'] * 100:.0f}%",
          "Conventional floor for a non-owner-occupied purchase"],
         ["Interest rate", f"{f['rate_base'] * 100:.2f}%",
          "7.55% national 30-yr average + investor premium"],
         ["Term", f"{f['term_years']} years", "Fixed, fully amortising"],
         ["Closing costs", f"{f['closing_costs_pct'] * 100:.0f}%",
          "Title, origination, survey, prepaids"],
         ["Vacancy", f"{o['vacancy_pct'] * 100:.0f}%",
          "About one month's turnover a year"],
         ["Maintenance + capex", f"{o['maintenance_capex_pct'] * 100:.0f}%",
          "Below the usual 10% because 11 of 12 are new build"],
         ["Management", f"{o['management_pct'] * 100:.0f}%",
          "Third-party; you are not local to three states"],
         ["Letting fee", "0%",
          "Deliberately excluded - would worsen every result"]],
        size=7.9)

    R.callout(
        "Two inputs could move these numbers more than anything else",
        "Property tax and insurance are modelled at market-typical levels, not "
        "quoted. Texas rates run 1.6-2.5%, but a MUD on a new subdivision can "
        "push past 3% - on a $290,000 house that single variable is about $120 a "
        "month. Gulf-coast and Louisiana insurance is similarly volatile: the "
        "$4,200 assumed for coastal Brazoria County and the $6,000 for Lake "
        "Charles are order-of-magnitude figures, and a $2,000 error either way "
        "is $167 a month. Both are asked for explicitly in every seller email.",
        tone="amber")

    R.h2("How the score is built", 10.4)
    R.body(
        f"Eighteen criteria, weighted to {res['weight_total']:.0f} points and "
        f"normalised to a 0-10 score. Financial performance carries "
        f"{res['financial_weight']:.0f} of those points, because for a "
        f"buy-and-hold investment it is the point of the exercise.", 8.8)
    R.space(4)
    ws = sorted(res["weights"].items(), key=lambda kv: -kv[1])
    NAMES = {"cashflow": "Monthly cash flow", "yield": "Capitalisation rate",
             "price_value": "Price per sqft vs set", "flood": "Flood exposure",
             "jobs": "Job market", "location": "Location quality",
             "workmanship": "Workmanship (judgement)",
             "goodwill": "Builder goodwill (judgement)",
             "schools": "School quality", "weather": "Weather / peril",
             "amenities": "Community amenities", "hoa": "HOA cost",
             "airport": "Airport access", "demographics": "Demographics",
             "population": "Population base", "distances": "Distance to facilities",
             "university": "University proximity", "walk": "Walk score"}
    half = (len(ws) + 1) // 2
    colw = (CW - 20) / 2
    ytop = R.y
    for col, chunk in enumerate((ws[:half], ws[half:])):
        yy = ytop
        x = M + col * (colw + 20)
        for k, w in chunk:
            R.pg.rect(x, yy - 2.0, (w / 18.0) * (colw - 112), 7.0,
                      fill=(0.62, 0.68, 0.80))
            R.pg.text(x + colw - 24, yy, f"{w:.0f}", "HB", 7.8, INK,
                      align="r", width=24)
            R.pg.text(x + (w / 18.0) * (colw - 112) + 6, yy, NAMES[k], "H", 7.8, INK)
            yy -= 13.2
    R.y = ytop - half * 13.2 - 10

    R.body(
        "Workmanship and builder goodwill are editorial judgements on public "
        "reputation and product positioning, not measured quality - no "
        "inspection was performed and none should be inferred. Walk score, "
        "demographics and school ratings are reasoned from the geography rather "
        "than pulled from the scoring services, and are the weakest criteria "
        "here. They carry 9 of 100 points between them for that reason.", 8.6,
        MUTED)

    # ---------------- page 4: inventory reconciliation ----------------
    R.new_page("What was in the folder", "inventory reconciliation")
    R.body(
        "Fourteen images resolved to twelve distinct properties. The "
        "reconciliation matters because two of the fourteen are not what they "
        "first appear.", 8.9)
    R.space(6)

    R.table(
        [("", 30, "c"), ("Count", 44, "c"), ("", 386, "l")],
        [["", str(rec["images_supplied"]), "Screenshots supplied in MMS-ITS/Houstonhome"],
         ["", "-1", "IMG_3502 duplicates IMG_3490 - same home, same zpid 440099886, shared twice"],
         ["", "-1", "IMG_3506 carries no link, no address and no caption - unidentifiable"],
         ["", "*" + str(rec["unique_identified_properties"]),
          "*Distinct properties that could be identified and researched"]],
        size=8.1, zebra=False)

    R.h2("Two of them are not individual houses", 10.4)
    R.body(
        "The Lafayette and Lake Charles links resolve to builder community and "
        "floor-plan pages rather than specific addresses. A plan has no lot, no "
        "completion date and no fixed price, so there is nothing to underwrite - "
        "they are options to build, not houses to buy.", 8.8)
    R.space(5)

    R.h2("Bedroom count against the brief", 10.4)
    R.body(
        f"The repository is named for a five-bedroom search. Of the twelve, "
        f"{rec['confirmed_5_bedroom']} are confirmed five-bedroom, "
        f"{rec['confirmed_not_5_bedroom']} are confirmed NOT "
        f"(Farmersville and Angleton are both four-bedroom), and "
        f"{rec['bedroom_count_unknown']} could not be established. The Lake "
        f"Charles community, on Redfin's description, tops out at four bedrooms "
        f"and 2,079 sqft - it may not meet the brief at all.", 8.8)
    R.space(5)

    R.h2("And the geography is not Houston", 10.4)
    R.body(
        "Six of the twelve are genuinely Houston metropolitan - Angleton, "
        "Dayton, Crosby, Cut and Shoot, Needville and Huffman. The rest are "
        "not. Farmersville and Cleburne are Dallas-Fort Worth, roughly 240 "
        "miles away. Snook and Caldwell are Bryan-College Station. Lafayette "
        "and Lake Charles are in Louisiana - a different state, different "
        "insurance market and different property tax regime. Nothing is wrong "
        "with a spread portfolio, but these are four distinct markets, and a "
        "single self-managed Houston strategy will not cover them.", 8.8)

    R.callout(
        "Open question before anything else",
        "Four states-worth of market, two listings that are plans rather than "
        "houses, two confirmed four-bedroom homes, and one screenshot nobody can "
        "identify. Worth confirming the search is actually scoped the way you "
        "intend it before putting money behind any of it.", tone="amber")

    # ---------------- property cards ----------------
    order = priced + unrank
    R.new_page("The properties, in rank order", "property cards")
    R.body(
        "Elevations are the images you supplied, cropped to the photograph. "
        "Several are builder renderings rather than photographs of the actual "
        "house - noted where so, because a rendering is a marketing asset and "
        "not evidence of what was built.", 8.5, MUTED)
    R.space(8)

    CARD_H = 228.0
    for idx, r in enumerate(order):
        if R.y - CARD_H < 54:
            R.new_page()
        card_top = R.y
        R.pg.rect(M, card_top - CARD_H, CW, CARD_H, fill=(0.985, 0.985, 0.99),
                  stroke=RULE, lw=0.6)

        # elevation
        iw, ih = 196.0, 132.0
        ix, iy = M + 10, card_top - 10 - ih
        name = r["image"].split(" /")[0].strip()
        R.pg.rect(ix - 1, iy - 1, iw + 2, ih + 2, fill=(0.88, 0.88, 0.9))
        R.pg.image(img(name), ix, iy, iw, ih, crop=CROPS.get(name))
        R.pg.text(ix, iy - 10, name, "H", 6.2, MUTED)

        tx = ix + iw + 14
        tw = CW - iw - 34
        yy = card_top - 20

        badge = f"RANK {r['rank']}" if r.get("rank") else "NOT RANKED"
        bcol = GREEN if r.get("rank") else AMBER
        R.pg.text(tx, yy, badge, "HB", 7.4, bcol)
        if r.get("score"):
            R.pg.text(tx, yy, f"SCORE {r['score']:.2f} / 10", "HB", 7.4, INK,
                      align="r", width=tw)
        elif r.get("provisional_score"):
            R.pg.text(tx, yy, f"PARTIAL {r['provisional_score']:.2f} "
                              f"({r['score_coverage'] * 100:.0f}% cover)",
                      "HB", 7.4, MUTED, align="r", width=tw)
        yy -= 14

        # Two entries are community/plan listings whose "address" field is a
        # sentence rather than an address; truncating it mid-word looked like a
        # bug, so the parenthetical is dropped and the fact is carried by the
        # 'a plan, not a house' flag instead.
        addr = r["address"].split(" (")[0]
        while P.text_width(addr, "HB", 10.6) > tw and len(addr) > 4:
            addr = addr[:-1]
        R.pg.text(tx, yy, addr, "HB", 10.6, INK)
        yy -= 12.5
        R.pg.text(tx, yy, r["label"], "H", 8.1, MUTED)
        yy -= 13

        spec = []
        if r.get("beds"):
            spec.append(f"{r['beds']} bed")
        if r.get("baths"):
            spec.append(f"{r['baths']:g} bath")
        if r.get("sqft"):
            spec.append(f"{r['sqft']:,} sqft")
        if r.get("ppsf"):
            spec.append(f"${r['ppsf']:.0f}/sqft")
        R.pg.text(tx, yy, "  -  ".join(spec) if spec else
                  "specification not established", "H", 8.2, INK)
        yy -= 12.5

        bl = f"{r['builder'].split(' (')[0]}  -  {r['community']}"
        if r.get("plan"):
            bl += f"  -  {r['plan'].split(' (')[0]} plan"
        for ln in P.wrap(bl, "H", 8.0, tw):
            R.pg.text(tx, yy, ln, "H", 8.0, MUTED)
            yy -= 11
        yy -= 3

        if r.get("price"):
            R.pg.text(tx, yy, money(r["price"]), "HB", 13.5, INK)
            conf = r["price_confidence"]
            R.pg.text(tx + P.text_width(money(r["price"]), "HB", 13.5) + 8, yy + 1,
                      f"({conf})", "H", 7.4,
                      MUTED if conf == "confirmed" else AMBER)
            yy -= 17
            cells = [
                ("Rent (est)", money(r["rent"])),
                ("Cap rate", pct(r["cap_rate"], 2)),
                ("Cash flow/mo", money(r["cf_base"])),
                ("DSCR", f"{r['dscr']:.2f}"),
                ("Cash needed", money(r["cash_in"])),
                ("Cash-on-cash", pct(r["coc_base"], 1)),
            ]
            cwid = tw / 3.0
            for i, (lab, val) in enumerate(cells):
                cx = tx + (i % 3) * cwid
                cy = yy - (i // 3) * 24
                R.pg.text(cx, cy, lab, "H", 6.6, MUTED)
                neg = val.startswith("-")
                R.pg.text(cx, cy - 10, val, "HB", 8.8, RED if neg else INK)
            yy -= 50
        else:
            R.pg.rect(tx, yy - 16, tw, 20, fill=AMBERBG)
            R.pg.text(tx + 6, yy - 10, "NO CONFIRMED PRICE - cannot be "
                                       "underwritten or ranked", "HB", 7.8, AMBER)
            yy -= 28

        flagmap = {
            "NOT_5BR": "not 5-bedroom", "NOT_HOUSTON": "outside Houston metro",
            "PRICE_UNCONFIRMED": "price unconfirmed", "RESALE": "resale, not new",
            "PHOTO_PLAN_MISMATCH": "photo contradicts plan",
            "SQFT_PRICE_DISCREPANCY": "sqft/price conflict",
            "BATH_COUNT_CONFLICT": "bath count conflict",
            "SPECS_UNKNOWN": "specification unknown",
            "PLAN_NOT_A_HOUSE": "a plan, not a house",
            "OUT_OF_STATE": "out of state", "BUILDER_DISPUTED": "builder disputed",
            "MAY_NOT_BE_5BR": "may not be 5-bed",
            "UNDER_CONSTRUCTION": "under construction",
            "PRICE_DERIVED": "price derived, not quoted",
            "BED_COUNT_INFERRED": "bed count inferred",
            "SQFT_APPROXIMATE": "sqft approximate",
            "UNIDENTIFIED": "unidentified",
        }
        fl = [flagmap.get(x, x.lower()) for x in r.get("flags", [])]
        if fl:
            fx = tx
            for t in fl:
                w = P.text_width(t, "H", 6.6) + 10
                if fx + w > tx + tw:
                    fx = tx
                    yy -= 13
                R.pg.rect(fx, yy - 3, w, 11, fill=REDBG)
                R.pg.text(fx + 5, yy, t, "H", 6.6, RED)
                fx += w + 4
            yy -= 15

        if r.get("flood_note"):
            for ln in P.wrap("Flood: " + r["flood_note"], "H", 7.2,
                             CW - 24)[:2]:
                R.pg.text(ix, yy, ln, "H", 7.2, MUTED)
                yy -= 10

        R.y = card_top - CARD_H - 12

    # ---------------- unidentified ----------------
    if excl:
        R.new_page("The screenshot that cannot be scored", "unidentified")
        e = excl[0]
        R.body(
            "IMG_3506 is the only image in the folder with no Zillow link, no "
            "address and no caption. It is a builder elevation rendering of a "
            "single-storey brick-and-stone home with a two-car garage. Without "
            "a location it cannot be priced, scored, or compared - and unlike "
            "the other thirteen it is full-bleed, with no WhatsApp chrome, so "
            "there is no surrounding context to recover an address from either.",
            8.9)
        R.space(10)
        iw = 330.0
        info = jpeg_info(ASSETS / "IMG_3506.jpeg")
        ih = iw * info["height"] / info["width"]
        R.pg.rect(M + (CW - iw) / 2 - 1, R.y - ih - 1, iw + 2, ih + 2,
                  fill=(0.88, 0.88, 0.9))
        R.pg.image(img("IMG_3506.jpeg"), M + (CW - iw) / 2, R.y - ih, iw, ih)
        R.y -= ih + 14
        R.pg.text(M, R.y, "IMG_3506.jpeg  -  1266 x 709  -  no link, no address",
                  "H", 7.2, MUTED, align="c", width=CW)
        R.y -= 24
        R.body("Either identify it or drop it from the comparison. If you still "
               "have the original WhatsApp thread, the message immediately "
               "before or after it will almost certainly carry the link.", 8.9)

    # ---------------- unverified ----------------
    R.new_page("What is not verified", "limits of this analysis")
    R.body(
        "Following the convention in your other repositories, this is the "
        "explicit list of what could not be confirmed. It is not a footnote - "
        "several of these could change a conclusion.", 8.9)
    R.space(8)

    R.h2("Could not be obtained at all", 10.2)
    R.bullets([
        "Any price for Farmersville, Cleburne, Snook, Needville, Huffman, "
        "Lafayette or Lake Charles - seven of twelve properties.",
        "The actual property tax rate on any individual parcel. County-typical "
        "rates are modelled; a MUD, PID or SUD could add more than a point.",
        "A single insurance quote. Every premium here is an estimate, and "
        "coastal Texas and Louisiana are the most volatile placements in the US.",
        "Confirmed HOA dues for any of the twelve.",
        "FEMA flood zone determinations per parcel - the exposure notes are "
        "from regional history, not from a map pull for these addresses.",
        "Property-level vacancy rates. A flat 8% is applied everywhere, which "
        "is likely optimistic in Caldwell and Snook where ownership dominates "
        "and the rental pool is thin.",
        "Walk Score, GreatSchools and Niche ratings as published numbers; "
        "school and walkability scores here are reasoned from geography.",
        "Lease restrictions in the HOA covenants. Some master-planned "
        "communities cap or forbid rentals outright, which would end the "
        "investment case for a given property regardless of its economics.",
    ], 8.4)

    R.h2("Known internal conflicts, left visible rather than smoothed over", 10.2)
    R.bullets([
        "Dayton: the supplied photograph shows a single-storey house, but every "
        "source describes the DRB Meyerson as a two-storey plan. One of the two "
        "is wrong.",
        "Crosby: Redfin's $111/sqft against 2,813 sqft implies about $312,000, "
        "which does not reconcile with the $290,990 list price ($103/sqft). One "
        "figure is stale.",
        "Cut and Shoot: Trulia says three bathrooms, the builder and Redfin say "
        "four. The builder-direct figure was preferred.",
        "Lake Charles: two different builders, D.R. Horton and DSLD Homes, both "
        "market a community of nearly this name in ZIP 70607 with different "
        "price ranges. Which one your link refers to is unresolved.",
        "Caldwell: Lennar and D.R. Horton both market a 'Whitetail Run' in "
        "Caldwell, with different plan sizes - the same name collision.",
        "Caldwell bed count: five is assembled from the layout description, not "
        "from any source stating '5 bedrooms'.",
    ], 8.4)

    R.h2("Modelling choices that flatter the result", 10.2)
    R.bullets([
        "Rent is lifted 15% above the published median to reflect the size of "
        "these houses. Without that premium every cash flow is roughly $230-330 "
        "a month worse.",
        "Maintenance is set at 8% rather than the customary 10%, on the basis "
        "that eleven of twelve are new build under warranty.",
        "Letting fees are excluded entirely.",
        "No allowance is made for the lease-up gap on the Huffman house, which "
        "is still under construction and will not produce rent on completion of "
        "a purchase.",
        "Appreciation is not modelled at all. On the available evidence that is "
        "the conservative choice: Conroe home values are down 1.0% year on year "
        "with homes taking about 70 days to go pending, and Burleson County is "
        "running 79 days on market.",
    ], 8.4)

    R.callout(
        "Read this before acting on any number in this document",
        "This is a desk study built from search-engine snippets, because every "
        "listing site blocked direct access. It is a tool for deciding which "
        "questions to ask and which properties to drop - not a substitute for "
        "the seller's own figures, a bindable insurance quote, a parcel tax "
        "statement, the HOA covenants, or an inspection. The emails accompanying "
        "this pack are written to collect exactly what is missing.", tone="amber")

    # ---------------- what would have to change ----------------
    R.new_page("What would have to change", "if you still want to proceed")
    R.body(
        "The arithmetic is not an argument against these markets, and not "
        "against buy-and-hold. It is an argument against buying these houses, "
        "at these prices, with this financing, today. Four things could change "
        "the answer.", 8.9)
    R.space(8)

    R.h2("1. Pay substantially less, or put substantially more down", 10.2)
    R.body(
        f"At {A['financing']['rate_base'] * 100:.2f}% the break-even deposit is "
        f"not 25% but something closer to 55-65% on these rent-to-price ratios. "
        f"Alternatively the price would have to fall far enough for the cap rate "
        f"to clear the mortgage rate - on Cut and Shoot that means roughly "
        f"{money(p6['noi_year'] / 0.0825)} against an asking price of "
        f"{money(p6['price'])}. Neither is a negotiation; both are a different "
        f"transaction.", 8.8)
    R.space(5)

    R.h2("2. Buy for appreciation and fund the deficit deliberately", 10.2)
    R.body(
        f"A conscious decision to carry {money(-best['cf_base_year'])} to "
        f"{money(-worst['cf_base_year'])} a year as the cost of holding land and "
        f"a new house in a growing metro is defensible - but it is a "
        f"speculation on price, not a rental investment, and it should be sized "
        f"against the fact that the nearest market with published data is "
        f"currently falling, not rising.", 8.8)
    R.space(5)

    R.h2("3. Harvest the builder incentives instead of the asset", 10.2)
    R.body(
        "Two builders in this set are already advertising rate buydowns: "
        "Trophy Signature in Farmersville at 3.25% (6.080% APR) with free "
        "appliances, and DSLD in Lake Charles at 3.99% initial (6.788% APR) with "
        "up to $12,000 toward costs. Note that DSLD's offer is tied to FHA, RD "
        "and VA products, none of which is available for an investment purchase "
        "- worth establishing what the investor-eligible equivalent is before "
        "treating it as a reason to prefer that community.", 8.8)
    R.space(5)

    R.h2("4. Change the product", 10.2)
    R.body(
        "Nothing in this set was selected for rental yield; these are family "
        "houses in exurban master-planned communities, which is the hardest "
        "product to make work as a leveraged rental at current rates. A smaller "
        "three-bedroom at half the price in an established rental submarket "
        "typically shows a materially better rent-to-price ratio than a "
        "3,000 sqft five-bedroom on the edge of the metro.", 8.8)

    R.space(6)
    R.h2("The immediate next step", 10.2)
    R.body(
        "Send the emails. Seven of twelve have no price at all, no HOA figure "
        "is confirmed, no tax rate is parcel-specific and no insurance is "
        "quoted. Those four gaps are worth more than any further desk analysis, "
        "and three of them are the inputs most likely to move the result.", 8.8)

    # ---------------- emails ----------------
    R.new_page("The eight emails", "drafted and ready in letters/")
    R.body(
        "Twelve properties, but eight recipients - Lennar alone accounts for "
        "five of the homes, so that approach is consolidated into a single "
        "letter which also presents you as a portfolio buyer rather than five "
        "separate enquiries.", 8.9)
    R.space(6)

    R.table(
        [("File", 118, "l"), ("Recipient", 108, "l"), ("Covers", 54, "c"),
         ("The question that matters most", 212, "l")],
        [["01-lennar-...", "Lennar (3 divisions)", "5",
          "Price for 4 of the 5; investor eligibility; MUD rates"],
         ["02-century-...", "Century Communities", "1",
          "Coastal Brazoria insurance quote and flood zone"],
         ["03-drb-homes-...", "DRB Homes", "1",
          "Why the photo shows one storey and the plan says two"],
         ["04-starlight-...", "Starlight Homes", "1",
          "Montgomery MUD rate; what is standard, not optional"],
         ["05-trophy-...", "Trophy Signature", "1",
          "Is the 3.25% offer open to an investor at all?"],
         ["06-dr-horton-...", "D.R. Horton (LA)", "1",
          "A specific address; tax without homestead exemption"],
         ["07-lake-charles-...", "DSLD and D.R. Horton", "1",
          "Which builder is it, and does a 5-bed even exist?"],
         ["08-cleburne-...", "Resale listing agent", "1",
          "Price, seller motivation, tax without homestead cap"]],
        size=7.7)

    R.h2("Four questions appear in every letter", 10.2)
    R.bullets([
        "The parcel's actual tax rate by taxing unit, including any MUD, PID "
        "or SUD, both today and at district build-out. This is the largest "
        "single unknown in the model - on a $290,000 house, 2.2% against 3.0% "
        "is about $190 a month.",
        "A bindable insurance quote rather than an estimate, with the wind, "
        "hail and named-storm deductibles spelled out. A $2,000 error here is "
        "$167 a month.",
        "Whether the HOA covenants permit letting at all - minimum lease term, "
        "a cap on the proportion of rented homes, a waiting period after "
        "closing. If a community forbids rentals, its economics are irrelevant, "
        "and this is asked before anything else for that reason.",
        "Whether the advertised incentive is available to an INVESTOR. Two "
        "builders here advertise headline rates that are tied to FHA, RD or VA "
        "financing, none of which an investment purchase can use. Each letter "
        "asks for the investor-eligible equivalent by name.",
    ], 8.4)

    R.callout(
        "The letters state the deficit openly",
        "Each email tells the builder or agent what my model shows and asks "
        "whether better information changes it. That is deliberate. It invites "
        "a serious counter-proposal rather than a brochure, it signals that an "
        "incentive would have to be substantial to matter, and on the one "
        "resale it opens the price conversation honestly instead of wasting "
        "two rounds getting there.", tone="amber")

    n = R.doc.save(OUT)
    return OUT, n, R.pageno


if __name__ == "__main__":
    path, size, pages = build()
    print(f"wrote {path.name}  {pages} A4 pages  {size / 1024:.0f} KB")
