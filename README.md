# Five-Bedroom Rental Investment Comparison

Twelve properties across Texas and Louisiana, scored for a long-term
buy-and-hold rental hold, built from the 14 listing screenshots in
[`MMS-ITS/Houstonhome`](https://github.com/MMS-ITS/Houstonhome).

## The headline

**None of the five properties with a confirmed price generates positive cash
flow at current investor mortgage rates, and none comes close.**

| | |
|---|---|
| Capitalisation rates | **1.50% – 2.92%** |
| Cost of investor debt | **~8.25%** |
| Monthly cash flow | **−$889 to −$1,577** |
| Annual cash flow | **−$10,668 to −$18,924** |
| DSCR | **0.22 – 0.43** (lenders want 1.20–1.25) |
| Properties passing the 1% rule | **0 of 12** |

This is negative leverage: the debt costs roughly three to five times what the
asset earns. A full percentage point off the mortgage rate moves cash flow by
about $140–190 a month against a shortfall of $890–1,580, so rate shopping
cannot close it.

## Contents

| File | What it is |
|------|-----------|
| [`Five-Bedroom-Rental-Comparison-A4.pdf`](Five-Bedroom-Rental-Comparison-A4.pdf) | **The artifact** — 13 numbered A4 pages with cropped frontal elevations, the ranked scorecard, the underwriting, and an explicit register of what is not verified |
| [`letters/`](letters) | **Eight email drafts**, one per seller or builder, ready to send |
| [`data/properties.json`](data/properties.json) | The 12 properties with per-field provenance and a price-confidence level on each |
| [`data/markets.json`](data/markets.json) | Rent, tax, flood, jobs, schools and liquidity per location, with rent provenance marked `researched` or `regional_proxy` |
| [`data/assumptions.json`](data/assumptions.json) | Every financing and operating input, each with its basis and source |
| [`data/results.json`](data/results.json) | Model output — written by `tools/model.py`, consumed by the report builder |
| [`assets/elevations/`](assets/elevations) | The 14 supplied screenshots, unmodified |
| [`tools/model.py`](tools/model.py) | Underwriting and scoring. Pure arithmetic, no hidden constants |
| [`tools/build_report.py`](tools/build_report.py) | Builds the PDF |
| [`tools/pdflib.py`](tools/pdflib.py) | Dependency-free A4 PDF writer (see below) |
| [`tools/jpeginfo.py`](tools/jpeginfo.py) | Reads JPEG dimensions from the SOF marker |
| [`tools/verify_pdf.py`](tools/verify_pdf.py) | 612 structural and layout assertions against the generated PDF |
| [`test/crosscheck.mjs`](test/crosscheck.mjs) | 204 assertions — an independent re-derivation of every figure |
| [`docs/SOURCES.md`](docs/SOURCES.md) | Source register, and an explicit list of what could not be verified |

## Rebuilding

```
python3 tools/model.py          # underwriting -> data/results.json
python3 tools/build_report.py   # -> Five-Bedroom-Rental-Comparison-A4.pdf
python3 tools/verify_pdf.py     # 612 structural + layout checks
node    test/crosscheck.mjs     # 204 assertions, independent implementation
```

Two deliberately separate implementations sharing no code, so the arithmetic
does not rest on one of them. `crosscheck.mjs` recomputes every published
figure in JavaScript from the raw inputs — including proving the amortisation
routine against a closed form and checking that the quoted break-even rent
really does produce zero cash flow — and `verify_pdf.py` parses the PDF back
from bytes to confirm a reader will actually open it.

## The ranking

Only the five properties with a usable price can be ranked. **These are
rankings among loss-making options, not endorsements.**

| # | Property | Builder | Price | Bed | Cap | Cash flow/mo | Score |
|---|----------|---------|------:|:---:|----:|-------------:|------:|
| 1 | Cut and Shoot, TX | Starlight Homes | $289,990 | 5 | 2.60% | −$1,006 | 5.12 |
| 2 | Caldwell, TX | Lennar | $277,750* | 5 | 2.92% | −$889 | 4.91 |
| 3 | Crosby, TX | Lennar | $290,990 | 5 | 2.37% | −$1,065 | 4.86 |
| 4 | Angleton, TX | Century Communities | $359,900 | 4 | 1.50% | −$1,577 | 3.63 |
| 5 | Dayton, TX | DRB Homes | $357,990 | 5 | 1.65% | −$1,525 | 3.35 |

\* derived arithmetically from $/sqft × sqft, not a quoted price.

The other seven have no obtainable price, so cash flow, yield and
price-per-sqft cannot be computed for them. They are **not** ranked against
these five — those three criteria carry 40 of the 100 weighting points and
every priced property scores badly on them, so a property with no price would
float to the top on missing data alone.

## Three things worth knowing before you read it

**It is not a Houston search.** Six of the twelve are Houston metro. Two are
Dallas–Fort Worth, ~240 miles away. Two are Bryan–College Station. Two are in
Louisiana — a different state, insurance market and tax regime.

**It is not entirely a five-bedroom search.** Six are confirmed five-bedroom,
two are confirmed four-bedroom (Farmersville and Angleton), and four could not
be established. The Lake Charles community may top out at four bedrooms.

**Two of the twelve are not houses.** The Lafayette and Lake Charles links
resolve to builder community and floor-plan pages, not addresses. A plan has no
lot, no completion date and no price. A thirteenth screenshot, `IMG_3506`, has
no link at all and could not be identified.

## Why the PDF is hand-rolled

This sandbox has no outbound network for package installs — `pip` and `npm`
both fail with a 403 through the proxy — and no browser engine, so neither
`reportlab` nor the headless-Chromium print path used in
[`MMS-ITS/-30K`](https://github.com/MMS-ITS/-30K) was available.
`tools/pdflib.py` writes PDF 1.4 bytes directly: the 14 standard Type1 fonts
with real Helvetica metrics so table figures align, and baseline JPEGs embedded
verbatim through `/DCTDecode`.

There is also no image library of any kind (no PIL, no ImageMagick), so the
elevations are cropped out of the WhatsApp screenshots using PDF clip paths and
a transform rather than by re-encoding pixels. The crop boxes in
`tools/build_report.py` were estimated by eye and set slightly generous, so a
sliver of chat chrome may show rather than risk slicing a roofline.

## Status

The analysis is complete and internally verified. It is a **desk study** built
from search-engine snippets, because Zillow, Redfin, Realtor, Trulia, Lennar
and NewHomeSource all return HTTP 403 to direct access from this environment.

No price is a quote, no tax rate is parcel-specific, no insurance premium is
bindable, and no HOA figure or flood determination is confirmed. The eight
emails in `letters/` are written to collect exactly those gaps — and the HOA
question is asked first in every one of them, because a community that forbids
letting makes its economics irrelevant.
