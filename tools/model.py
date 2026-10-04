#!/usr/bin/env python3
"""Underwriting and scoring model.

Reads data/properties.json, data/markets.json, data/assumptions.json and
writes data/results.json. Pure arithmetic, no network, no hidden constants:
every rate and ratio comes from assumptions.json.

Run:  python3 tools/model.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"


def load():
    props = json.loads((D / "properties.json").read_text())
    markets = json.loads((D / "markets.json").read_text())
    assume = json.loads((D / "assumptions.json").read_text())
    return props, markets, assume


def pmt(principal, annual_rate, years):
    """Level monthly payment on a fully amortising loan."""
    if principal <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = years * 12
    if r == 0:
        return principal / n
    g = (1 + r) ** n
    return principal * r * g / (g - 1)


# Builder assessment. These are explicit editorial judgements on public
# reputation and product positioning, NOT measured workmanship. They are the
# softest numbers in the model and are labelled as such in the report.
BUILDERS = {
    "Lennar": {
        "workmanship": 6.0, "goodwill": 6.5,
        "note": "Largest US homebuilder by volume. Deep warranty infrastructure and an 'Everything's Included' specification, but a mass-production model and mixed owner reports on finish quality.",
    },
    "D.R. Horton": {
        "workmanship": 5.5, "goodwill": 6.0,
        "note": "Highest-volume US builder by closings. Entry-level positioning, value-engineered specification.",
    },
    "Century Communities": {
        "workmanship": 6.5, "goodwill": 6.0,
        "note": "Top-ten national builder. Mid-market specification; the Sinclair at 3,075 sqft is the largest home in this set.",
    },
    "DRB Homes": {
        "workmanship": 6.0, "goodwill": 5.5,
        "note": "Mid-size builder, part of the Dream Finders group. Markets River Ranch on personalisation options.",
    },
    "Starlight Homes (Ashton Woods' entry-level brand)": {
        "workmanship": 5.0, "goodwill": 5.5,
        "note": "Ashton Woods' entry-level brand, explicitly built to an affordable price point. Expect value-engineered specification; the parent has a stronger reputation than the sub-brand.",
    },
    "Trophy Signature Homes": {
        "workmanship": 7.0, "goodwill": 6.5,
        "note": "Green Brick Partners' DFW-focused brand. Generally the best-regarded builder in this set, and the only one currently advertising a 3.25% (6.080% APR) rate promotion plus free appliances.",
    },
    "DISPUTED - see caution": {
        "workmanship": 5.0, "goodwill": 4.0,
        "note": "Builder identity unresolved between D.R. Horton and DSLD Homes. Scored down for the uncertainty itself - you cannot assess a builder you have not identified.",
    },
    "NHC (original builder); now a resale": {
        "workmanship": 5.0, "goodwill": 4.5,
        "note": "Original builder NHC. As a resale there is no builder relationship, no incentive package and reduced warranty runway; against that, the seller is an individual and the price is already cut.",
    },
}

# Per-property qualitative scores, 0-10. Assembled from markets.json findings.
# Where the underlying datum was not obtainable the score is deliberately
# held near the middle rather than guessed high or low.
QUAL = {
    #        loc  amen air  sch  uni  walk demo jobs  pop  dist weath flood
    "P01": dict(location=7.5, amenities=5.5, airport=6.5, schools=5.5, university=4.0, walk=2.5, demographics=8.0, jobs=8.5, population=7.0, distances=5.5, weather=6.0, flood=7.5),
    "P02": dict(location=6.0, amenities=5.5, airport=6.0, schools=5.5, university=3.5, walk=2.5, demographics=6.5, jobs=5.5, population=5.0, distances=5.0, weather=3.0, flood=2.5),
    "P03": dict(location=5.5, amenities=7.0, airport=6.5, schools=5.0, university=4.0, walk=2.0, demographics=5.0, jobs=6.0, population=5.5, distances=5.0, weather=4.5, flood=3.5),
    "P04": dict(location=7.0, amenities=8.0, airport=7.5, schools=5.5, university=5.0, walk=2.5, demographics=5.5, jobs=7.5, population=6.5, distances=6.5, weather=4.0, flood=3.0),
    "P05": dict(location=6.5, amenities=5.0, airport=6.0, schools=5.5, university=5.0, walk=3.0, demographics=6.0, jobs=7.0, population=6.0, distances=5.5, weather=5.5, flood=7.5),
    "P06": dict(location=7.5, amenities=5.5, airport=8.5, schools=7.0, university=5.5, walk=2.5, demographics=6.5, jobs=8.5, population=8.0, distances=7.0, weather=4.0, flood=3.5),
    "P07": dict(location=4.0, amenities=3.5, airport=3.0, schools=6.0, university=6.5, walk=1.5, demographics=4.0, jobs=5.5, population=2.5, distances=3.0, weather=6.0, flood=6.5),
    "P08": dict(location=4.5, amenities=5.0, airport=4.0, schools=4.0, university=7.5, walk=2.5, demographics=4.5, jobs=4.0, population=5.0, distances=4.5, weather=2.5, flood=2.0),
    "P09": dict(location=6.5, amenities=7.0, airport=5.5, schools=6.5, university=4.5, walk=2.0, demographics=7.0, jobs=7.0, population=6.0, distances=5.0, weather=4.0, flood=3.0),
    "P10": dict(location=6.5, amenities=7.0, airport=7.5, schools=5.5, university=4.5, walk=2.0, demographics=5.5, jobs=7.0, population=6.0, distances=6.0, weather=4.0, flood=2.5),
    "P11": dict(location=4.0, amenities=4.5, airport=4.0, schools=4.0, university=6.0, walk=2.5, demographics=4.0, jobs=3.5, population=4.0, distances=4.5, weather=1.5, flood=1.5),
    "P12": dict(location=4.5, amenities=3.5, airport=3.0, schools=6.5, university=6.5, walk=1.5, demographics=4.5, jobs=5.5, population=2.5, distances=3.0, weather=6.0, flood=6.5),
}

WEIGHTS = {
    "cashflow":     18.0,
    "yield":        12.0,
    "price_value":  10.0,
    "flood":         8.0,
    "jobs":          7.0,
    "location":      7.0,
    "workmanship":   6.0,
    "goodwill":      4.0,
    "schools":       5.0,
    "weather":       4.0,
    "amenities":     3.0,
    "hoa":           3.0,
    "airport":       3.0,
    "demographics":  3.0,
    "population":    2.0,
    "distances":     2.0,
    "university":    2.0,
    "walk":          1.0,
}


def score_price_value(ppsf, all_ppsf):
    """Cheaper per square foot scores higher, scaled across the set."""
    if ppsf is None:
        return None
    lo, hi = min(all_ppsf), max(all_ppsf)
    if hi == lo:
        return 7.0
    return 10.0 - 8.0 * (ppsf - lo) / (hi - lo)


def score_cashflow(cf_month):
    """0 at -$1,600/mo, 5 at break-even, 10 at +$400/mo."""
    if cf_month is None:
        return None
    if cf_month >= 400:
        return 10.0
    if cf_month <= -1600:
        return 0.0
    if cf_month >= 0:
        return 5.0 + 5.0 * (cf_month / 400.0)
    return 5.0 * (1.0 - (-cf_month) / 1600.0)


def score_yield(cap):
    """0 at 1.5% cap, 10 at 7.5% cap."""
    if cap is None:
        return None
    return max(0.0, min(10.0, (cap - 0.015) / (0.075 - 0.015) * 10.0))


def score_hoa(hoa_annual):
    if hoa_annual is None:
        return None
    return max(0.0, min(10.0, 10.0 - (hoa_annual / 150.0)))


def run():
    props, markets, A = load()
    fin = A["financing"]
    op = A["operating"]
    taxes = A["tax_rates"]
    ins = A["insurance_annual"]
    hoas = A["hoa_annual"]
    mkts = markets["markets"]

    rows = []
    for p in props["properties"]:
        pid = p["id"]
        if pid not in mkts:
            rows.append({"id": pid, "excluded": True,
                         "reason": "Unidentified - no address, no link, nothing to model.",
                         "address": p["address"], "image": p["image"]})
            continue

        m = mkts[pid]
        price = p.get("price")
        sqft = p.get("sqft")
        rent = m.get("rent_estimate")

        rec = {
            "id": pid,
            "excluded": False,
            "address": p["address"],
            "label": m["label"],
            "metro": m["metro"],
            "image": p["image"],
            "builder": p["builder"],
            "community": p["community"],
            "plan": p["plan"],
            "beds": p["beds"], "baths": p["baths"], "sqft": sqft,
            "construction": p["construction"],
            "price": price,
            "price_confidence": p["price_confidence"],
            "flags": p.get("flags", []),
            "caution": p.get("caution"),
            "rent": rent,
            "rent_basis": m["rent_basis"],
            "tax_rate": taxes[m["tax_key"]],
            "insurance": ins[m["ins_key"]],
            "hoa": hoas[m["hoa_key"]],
            "flood_note": m["flood"],
            "liquidity": m.get("liquidity"),
            "university": m.get("university"),
            "airport": m.get("airport"),
            "notes": m.get("notes"),
        }

        b = BUILDERS.get(p["builder"], {"workmanship": 5.0, "goodwill": 5.0, "note": ""})
        rec["builder_note"] = b["note"]

        if price:
            rec["ppsf"] = round(price / sqft, 1) if sqft else None
            down = price * fin["down_payment_pct"]
            loan = price - down
            rec["down"] = round(down)
            rec["loan"] = round(loan)
            rec["closing"] = round(price * fin["closing_costs_pct"])
            rec["cash_in"] = round(down + price * fin["closing_costs_pct"])

            for tag, rate in (("base", fin["rate_base"]),
                              ("low", fin["rate_low"]),
                              ("high", fin["rate_high"])):
                rec[f"pi_{tag}"] = round(pmt(loan, rate, fin["term_years"]))

            tax_m = price * rec["tax_rate"] / 12.0
            ins_m = rec["insurance"] / 12.0
            hoa_m = rec["hoa"] / 12.0
            rec["tax_month"] = round(tax_m)
            rec["ins_month"] = round(ins_m)
            rec["hoa_month"] = round(hoa_m)

            if rent:
                leak = op["vacancy_pct"] + op["maintenance_capex_pct"] + op["management_pct"]
                egi_m = rent * (1 - leak)
                rec["leak_pct"] = leak
                rec["egi_month"] = round(egi_m)
                noi_y = egi_m * 12 - (price * rec["tax_rate"]) - rec["insurance"] - rec["hoa"]
                rec["noi_year"] = round(noi_y)
                rec["cap_rate"] = round(noi_y / price, 4)

                for tag in ("base", "low", "high"):
                    cf = egi_m - rec[f"pi_{tag}"] - tax_m - ins_m - hoa_m
                    rec[f"cf_{tag}"] = round(cf)
                    rec[f"cf_{tag}_year"] = round(cf * 12)

                rec["coc_base"] = round(rec["cf_base_year"] / rec["cash_in"], 4)
                ads = rec["pi_base"] * 12
                rec["dscr"] = round(noi_y / ads, 3) if ads else None
                rec["one_pct_rent_needed"] = round(price * 0.01)
                rec["one_pct_ratio"] = round(rent / price, 5)
                rec["breakeven_rent"] = round(
                    (rec["pi_base"] + tax_m + ins_m + hoa_m) / (1 - leak)
                )
            else:
                for k in ("cap_rate", "cf_base", "dscr"):
                    rec[k] = None
        else:
            rec["ppsf"] = None
            for k in ("cap_rate", "cf_base", "dscr", "cf_low", "cf_high"):
                rec[k] = None

        rec["q"] = dict(QUAL[pid])
        rec["q"]["workmanship"] = b["workmanship"]
        rec["q"]["goodwill"] = b["goodwill"]
        rows.append(rec)

    # ---- scoring, once the whole set is known ----
    live = [r for r in rows if not r["excluded"]]
    all_ppsf = [r["ppsf"] for r in live if r.get("ppsf")]

    for r in live:
        q = r["q"]
        q["price_value"] = score_price_value(r.get("ppsf"), all_ppsf) if all_ppsf else None
        q["cashflow"] = score_cashflow(r.get("cf_base"))
        q["yield"] = score_yield(r.get("cap_rate"))
        q["hoa"] = score_hoa(r.get("hoa"))

        total_w = 0.0
        acc = 0.0
        missing = []
        for crit, w in WEIGHTS.items():
            v = q.get(crit)
            if v is None:
                missing.append(crit)
                continue
            acc += v * w
            total_w += w
        r["score"] = round(acc / total_w, 2) if total_w else None
        r["score_coverage"] = round(total_w / sum(WEIGHTS.values()), 3)
        r["score_missing"] = missing

    # Only fully-scored properties may be ranked against each other.
    #
    # This matters. The financial criteria (cashflow, yield, price_value) carry
    # 40 of the 100 weight points and every property scores BADLY on them. A
    # property with no price simply omits those criteria, so its average is
    # computed over the remaining, kinder 60 points and it floats to the top on
    # missing data alone. Ranking the two groups together would hand first place
    # to the properties we know least about, which is exactly backwards.
    FULL = 0.999
    ranked = sorted(
        [r for r in live if r.get("score") is not None
         and r.get("score_coverage", 0) >= FULL],
        key=lambda r: -r["score"],
    )
    for i, r in enumerate(ranked, 1):
        r["rank"] = i

    unrankable = sorted(
        [r for r in live if r.get("score_coverage", 0) < FULL],
        key=lambda r: -(r.get("score") or 0),
    )
    for r in unrankable:
        r["rank"] = None
        r["provisional_score"] = r.pop("score", None)
        r["unrankable_reason"] = (
            "No confirmed price, so cash flow, yield and price-per-sqft cannot be "
            "computed. The partial score below covers only "
            f"{r.get('score_coverage', 0) * 100:.0f}% of the weighting and is NOT "
            "comparable with the ranked properties - it omits precisely the "
            "criteria on which every priced property scores worst."
        )

    out = {
        "generated": "2026-10-04",
        "weights": WEIGHTS,
        "weight_total": sum(WEIGHTS.values()),
        "financial_weight": WEIGHTS["cashflow"] + WEIGHTS["yield"] + WEIGHTS["price_value"],
        "builders": BUILDERS,
        "rows": rows,
        "ranked_ids": [r["id"] for r in ranked],
        "unrankable_ids": [r["id"] for r in unrankable],
        "excluded_ids": [r["id"] for r in rows if r["excluded"]],
    }
    (D / "results.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    res = run()
    print(f"{'ID':4} {'Location':34} {'Price':>9} {'Rent':>6} {'P&I':>6} "
          f"{'Cap':>6} {'CF/mo':>7} {'DSCR':>6} {'Score':>6} {'Cov':>5}")
    print("-" * 104)
    order = (res["ranked_ids"] + res["unrankable_ids"] + res["excluded_ids"])
    by_id = {r["id"]: r for r in res["rows"]}
    for pid in order:
        r = by_id[pid]
        if r["excluded"]:
            print(f"{r['id']:4} {'UNIDENTIFIED - excluded from all scoring':44}")
            continue
        if r.get("rank") is None:
            ps = r.get("provisional_score")
            print(f"{r['id']:4} {r['label'][:34]:34} {'NO PRICE':>9} "
                  f"{'$' + format(r['rent'], ','):>6} {'-':>6} {'-':>6} {'-':>7} "
                  f"{'-':>6} {'(' + format(ps, '.2f') + ')':>6} "
                  f"{r['score_coverage']*100:.0f}%")
            continue
        price = f"${r['price']:,}" if r.get("price") else "n/a"
        rent = f"${r['rent']:,}" if r.get("rent") else "n/a"
        pi = f"${r['pi_base']:,}" if r.get("pi_base") else "n/a"
        cap = f"{r['cap_rate']*100:.2f}%" if r.get("cap_rate") else "n/a"
        cf = f"${r['cf_base']:,}" if r.get("cf_base") is not None else "n/a"
        dscr = f"{r['dscr']:.2f}" if r.get("dscr") else "n/a"
        sc = f"{r['score']:.2f}" if r.get("score") else "n/a"
        cov = f"{r['score_coverage']*100:.0f}%" if r.get("score_coverage") else "n/a"
        print(f"{r['id']:4} {r['label'][:34]:34} {price:>9} {rent:>6} {pi:>6} "
              f"{cap:>6} {cf:>7} {dscr:>6} {sc:>6} {cov:>5}")
