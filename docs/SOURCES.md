# Source register

Every external figure used in the report, with the query that produced it, and
an explicit list of what could not be verified.

## Access constraints that shaped the whole method

Direct page fetches were attempted first and **all failed**:

| Target | Result |
|---|---|
| `zillow.com/homedetails/...` | HTTP 403 |
| `lennar.com/new-homes/...` (two URLs) | HTTP 403 |
| `newhomesource.com/specdetail/...` | HTTP 403 |
| `realtor.com/realestateandhomes-detail/...` | HTTP 403 |

Consequently **no figure in this report was read from a listing page.**
Everything comes from web-search result snippets. Where a snippet quoted an
exact price, it is marked `confirmed`; where two published figures were
multiplied together, `derived`; otherwise `range_only` or `unknown`.

The sandbox also reported `network_mode: INTEGRATIONS_ONLY`, so `pip install`
and `npm install` fail (403 through the proxy). No PDF library, no browser
engine and no image library were available — hence the hand-rolled
`tools/pdflib.py`.

## Interest rates — 4 October 2026

| Figure | Source |
|---|---|
| 30-yr fixed national average **7.55% APR** | [Bankrate, investment property rates](https://www.bankrate.com/mortgages/investment-property-rates/) |
| 30-yr fixed **7.38%** weekly survey | [Bankrate, 30-year rates](https://www.bankrate.com/mortgages/30-year-mortgage-rates/) |
| Top-tier 30-yr fixed index **7.57%** | [Mortgage News Daily](https://www.mortgagenewsdaily.com/mortgage-rates) |
| Investor loans price **0.5–1.0 pt above** primary | [LendingTree](https://www.lendingtree.com/home/mortgage/investment-property-mortgage-rates/), [The Mortgage Reports](https://themortgagereports.com/27698/investment-property-mortgage-rates-how-much-more-will-you-pay) |
| Rates at their highest since 2023 | [The Mortgage Reports, 3 Oct 2026](https://themortgagereports.com/mortgage-rates-now/mortgage-rates-today-october-3-2026) |

Modelled central case **8.25%**, band 7.75–8.75%.

## Property tax

| Figure | Source |
|---|---|
| Texas averages **1.6–2.5%**; new builds in MUD districts can exceed **3%** | [LRG Realty, new-build tax reality check](https://lrgrealty.com/tools/texas-new-build-taxes-hoa-reality-check/) |
| Official per-taxing-unit rate register | [Texas Comptroller](https://comptroller.texas.gov/taxes/property-tax/rates/) |
| Live MUD levies confirmed in Brazoria County | [Brazoria County tax estimator](https://tax.brazoriacountytx.gov/TaxEstimator), [BC MUD 21](https://www.bcmud21.com/tax-matters/) |

County-typical rates were modelled. **No parcel-specific rate was obtained for
any of the twelve properties.**

## Rent and market data

Only four of twelve locations yielded a published rent median. The rest are
reasoned regional proxies and are marked `regional_proxy` in
`data/markets.json`.

| Location | Figure | Source |
|---|---|---|
| ZIP 77303 (Cut and Shoot) | median rent **$1.8K/mo** | [Realtor.com 77303](https://www.realtor.com/local/market/texas/zipcode-77303) |
| Conroe | median rent **$1.9K/mo**, +3.95% YoY | [Realtor.com Conroe](https://www.realtor.com/local/market/texas/montgomery-county/conroe) |
| Conroe | 4-bed townhome avg **$2,450** | [Trulia Conroe rent trends](https://www.trulia.com/average-rent-market-trends/conroe-tx/) |
| Conroe | home value **$311,472, down 1.0% YoY**, ~70 days to pending | [Zillow Conroe](https://www.zillow.com/home-values/817272/conroe-tx/) |
| ZIP 77515 (Angleton) | median rent **$1.9K/mo** | [Realtor.com 77515](https://www.realtor.com/local/market/texas/zipcode-77515) |
| Angleton | median rent **$1.8K**, +23.12% YoY, 62 days on market | [Realtor.com Angleton](https://www.realtor.com/local/market/texas/brazoria-county/angleton) |
| Angleton | median list price **$263,500** | [Zillow Angleton](https://www.zillow.com/angleton-tx/home-values/) |
| Angleton | median income **$86,712** | [HomeSnacks](https://www.homesnacks.com/tx/angleton-cost-of-living/) |
| Caldwell | median rent **$1,500** | [Zillow Rental Manager](https://www.zillow.com/rental-manager/market-trends/caldwell-tx/) |
| Burleson County | median list **$302K**, median rent **$1.4K**, **79 days** on market | [Realtor.com Burleson County](https://www.realtor.com/local/market/texas/burleson-county) |
| Caldwell | population **12,670**, median home value **$215,100** | [Texas Ally](https://www.texasally.com/neighborhoods/burleson/caldwell) |
| Caldwell | **22 miles** from Bryan/College Station and Texas A&M | [DowntownTX](https://downtowntx.org/caldwell-texas) |
| Caldwell | schools highly rated; most residents own their homes | [Niche](https://niche.com/places-to-live/caldwell-burleson-tx) |

## Per-property identification

| ID | Property | Key sources |
|---|---|---|
| P01 | 4003 Somerville Dr, Farmersville | [Redfin](https://www.redfin.com/TX/Farmersville/4003-Somerville-Dr-75442/home/203201620) (4bd/3ba); [Trophy Signature Lakehaven](https://www.trophysignaturehomes.com/communities/farmersville/lakehaven) ($239,990–$419,990; 3.25%/6.080% APR + free appliances) |
| P02 | 117 Bayou Bend Ct, Angleton | [Trulia Bayou Bend](https://www.trulia.com/builder-community/bayou-bend--31163527) (**$359,900**, 4bd/3.5ba, 3,075 sqft); [Realtor.com](https://www.realtor.com/realestateandhomes-detail/117-Bayou-Bend-Ct_Angleton_TX_77515_M90932-28827) (Sinclair plan); [Homes.com](https://www.homes.com/new-homes/community/bayou-bend/kvnts5g9w7kc0/) (Century Communities, $270K–$370K) |
| P03 | 214 Cross Gable Ln, Dayton | [HAR flyer MLS 87266577](https://www.har.com/flyer/2/mlnum/87266577) (**$357,990**); [Redfin](https://www.redfin.com/TX/Dayton/214-Cross-Gable-Ln-77535/home/198521410) (Meyerson, 5bd/3ba); [DRB plan page](https://www.drbhomes.com/drbhomes/find-your-home/communities/texas/houston/river-ranch/home-plans/meyerson/floorplan) (2,740 sqft); [Trulia](https://www.trulia.com/builder-community-plan/river-ranch-meyerson-460911397) ($327,990+ base) |
| P04 | 1726 Primrose Pointe Dr, Crosby | [Trulia Synova Majors](https://www.trulia.com/builder-community/synova-majors-collection--32062252) (**$290,990**, 5bd/4ba, 2,813 sqft); [Redfin community](https://www.redfin.com/TX/Crosby/Synova-Majors-Collection/community/46569638) (Lennar, amenities) |
| P05 | 820 Sugartree Dr, Cleburne | [Redfin](https://www.redfin.com/TX/Cleburne/820-Sugartree-Dr-76031/home/190643207) (NHC, Adams/Liberty Series, 5bd/2.5ba, >3,000 sqft, MLS 20608797); [Realtor.com](https://www.realtor.com/realestateandhomes-detail/820-Sugartree-Dr_Cleburne_TX_76031_M95758-45935) (resale, price cut $5K) |
| P06 | 5646 Shelford Birch Dr, Cut and Shoot | [**Starlight Homes, builder-direct**](https://www.starlighthomes.com/houston/avalon-ridge/pioneer) (**$289,990**, 5bd/4ba, 2,776 sqft); [Redfin](https://www.redfin.com/TX/Cut-and-Shoot/5646-Shelford-Birch-Dr-77303/home/202098467) |
| P07 | 173 Cotton Cv, Snook | [Redfin](https://www.redfin.com/city/17604/TX/Somerville/5-bedrooms) (Lennar Grand Lake Classic Collection, "coming soon"); [Trulia Snook](https://www.trulia.com/TX/Snook/) ($260,990+) |
| P08 | Stable View, Lafayette LA | [Zillow Rosemont plan](https://www.zillow.com/community/stable-view/347158307_zpid/) (5bd/3ba, two-storey); [Trulia](https://www.trulia.com/builder-community/stable-view--30112649) ($230,500–$323,500); [Realtor.com](https://www.realtor.com/community-detail/Stable-View_102-Stable-View-Drive_Lafayette_LA_70507_Q717000086090) (D.R. Horton, Carencro) |
| P09 | 6515 Little Yellow Ct, Needville | [Lennar Monarch Landing](https://www.lennar.com/new-homes/texas/houston/needville/monarch-landing6/majors-collection/dimaggio/22686601156) (neighbouring homesites only) |
| P10 | 722 Pescarola Dr, Huffman | [Lennar Canon](https://www.lennar.com/new-homes/texas/houston/huffman/sila/bristol-coastline-collections/canon/22775515408) (under construction); [Redfin](https://www.redfin.com/TX/Huffman/733-Perscarola-Dr-77336/home/205477207) ($122/sqft nearby) |
| P11 | Crest at Morganfield, Lake Charles LA | [Redfin](https://www.redfin.com/LA/Lake-Charles/Crest-at-Morganfield/community/4148) (D.R. Horton, 3–4bd, 1,447–2,079 sqft); [Trulia](https://www.trulia.com/builder-community/crest-at-morganfield--40467) ($233,500–$324,500); [DSLD Homes](https://www.dsldhomes.com/communities/louisiana/lake-charles/the-crest-at-morganfield) (3.99%/6.788% APR, FHA/RD/VA, $12,000); [NewHomeSource](https://www.newhomesource.com/basiccommunity/community-222745/the-crest-at-morganfield-lake-charles-la-70607) ($229,990–$267,990) |
| P12 | 109 Peluce Pl, Caldwell | [Lennar Ruth plan](https://www.lennar.com/new-homes/texas/bryan-college-station/caldwell/whitetail-run/majors-collection/ruth) (**2,750 sqft**); [Redfin](https://www.redfin.com/TX/Caldwell/109-Peluce-Pl-77836/home/202398230) ($101/sqft); [Realtor.com](https://www.realtor.com/realestateandhomes-detail/109-Peluce-Pl_Caldwell_TX_77836_M90813-42354) (layout); [Trulia](https://www.trulia.com/builder-community/whitetail-run-majors-collection--32246435) ($212,990–$288,990) |
| P13 | `IMG_3506.jpeg` | **None.** No link, no address, no caption. |

---

# What could not be verified

## No data obtainable

- **Any price** for Farmersville, Cleburne, Snook, Needville, Huffman,
  Lafayette or Lake Charles — **seven of twelve**.
- **The actual tax rate on any individual parcel.** County-typical rates are
  modelled; a MUD, PID or SUD could add more than a percentage point.
- **A single insurance quote.** Every premium is an estimate.
- **Confirmed HOA dues** for any of the twelve.
- **FEMA flood zone determinations** per parcel. Exposure notes are from
  regional history, not a map pull for these addresses.
- **Property-level vacancy rates.** A flat 8% is applied everywhere — likely
  optimistic in Caldwell and Snook, where ownership dominates.
- **Walk Score, GreatSchools and Niche ratings** as published numbers. School
  and walkability scores are reasoned from geography. They carry 9 of 100
  weighting points for that reason.
- **HOA lease restrictions.** Some master-planned communities cap or forbid
  rentals outright, which would end the investment case regardless of
  economics. Asked first in every email.
- Bedroom, bathroom and square-footage specification for Snook, Needville,
  Huffman and Lake Charles.

## Known conflicts, left visible rather than smoothed over

1. **Dayton** — the supplied photo shows a single-storey house; every source
   describes the DRB Meyerson as two-storey. One is wrong.
2. **Crosby** — Redfin's $111/sqft × 2,813 sqft implies ~$312,000, which does
   not reconcile with the $290,990 list price ($103/sqft). One figure is stale.
3. **Cut and Shoot** — Trulia says 3 bathrooms; the builder and Redfin say 4.
   Builder-direct preferred.
4. **Lake Charles** — "Crest at Morganfield" (D.R. Horton) and "The Crest at
   Morganfield" (DSLD Homes) are both marketed in ZIP 70607 with different
   price ranges. Unresolved.
5. **Caldwell** — Lennar *and* D.R. Horton both market a "Whitetail Run" in
   Caldwell, with different plan sizes. Same name collision.
6. **Caldwell bed count** — five is assembled from the layout description, not
   from any source stating "5 bedrooms".
7. **Angleton** — do not confuse 117 Bayou Bend **Court** (Sinclair, 4bd,
   3,075 sqft, $359,900) with 117 Bayou Bend **Boulevard** (Carlsbad, 3bd,
   2,220 sqft, $334,900).

## Modelling choices that flatter the result

- Rent is lifted **15%** above the published median for house size. Without
  it, every cash flow is ~$230–330/mo worse.
- Maintenance is **8%**, not the customary 10%, because 11 of 12 are new build.
- **Letting fees are excluded entirely.**
- No lease-up gap is modelled for the Huffman house, still under construction.
- **Appreciation is not modelled at all.** On the evidence that is the
  conservative choice — Conroe values are down 1.0% YoY at ~70 days to
  pending, and Burleson County is at 79 days on market.

## Judgement calls, not findings

- **Workmanship and builder goodwill** scores are editorial assessments of
  public reputation and product positioning. No inspection was performed and
  none should be inferred.
- Airport, university and facility distances are approximate road distances
  from general geography, not measured routes.
- The **crop boxes** for the elevation images were estimated by eye, since no
  image library was available to measure with.
