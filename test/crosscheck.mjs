#!/usr/bin/env node
/**
 * Independent re-derivation of every published figure.
 *
 * This shares no code with tools/model.py. It reads only the raw inputs
 * (properties.json, markets.json, assumptions.json), recomputes the
 * underwriting from first principles, and asserts that results.json matches.
 * The point is that the numbers in the PDF do not rest on a single
 * implementation being correct.
 *
 * Run:  node test/crosscheck.mjs
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => JSON.parse(readFileSync(join(ROOT, p), "utf8"));

const props = read("data/properties.json");
const markets = read("data/markets.json").markets;
const A = read("data/assumptions.json");
const results = read("data/results.json");

let pass = 0;
const fails = [];

function eq(label, got, want, tol = 0) {
  if (got === null || got === undefined || want === null || want === undefined) {
    if (got === want || (got == null && want == null)) { pass++; return; }
    fails.push(`${label}: got ${got}, want ${want}`);
    return;
  }
  if (Math.abs(got - want) <= tol) pass++;
  else fails.push(`${label}: got ${got}, want ${want} (tol ${tol})`);
}

function truthy(label, cond) {
  if (cond) pass++;
  else fails.push(label);
}

// --- amortisation, derived independently of the Python ---
// Standard annuity: A = P * i / (1 - (1+i)^-n)
function monthlyPayment(principal, annualRate, years) {
  const i = annualRate / 12;
  const n = years * 12;
  if (i === 0) return principal / n;
  return (principal * i) / (1 - Math.pow(1 + i, -n));
}

// Sanity-check the amortisation routine itself against a known closed form:
// a loan at 0% must repay exactly principal/n, and the final balance of an
// amortised loan must reach zero.
{
  eq("amort: zero-rate", monthlyPayment(120000, 0, 10), 1000, 1e-9);
  let bal = 217493;
  const r = 0.0825 / 12;
  const pmt = monthlyPayment(bal, 0.0825, 30);
  for (let k = 0; k < 360; k++) bal = bal * (1 + r) - pmt;
  truthy(`amort: balance amortises to zero (got ${bal.toFixed(4)})`,
    Math.abs(bal) < 0.05);
}

const byId = Object.fromEntries(results.rows.map((r) => [r.id, r]));
const fin = A.financing;
const op = A.operating;

let modelled = 0;

for (const p of props.properties) {
  const m = markets[p.id];
  const r = byId[p.id];
  truthy(`${p.id}: present in results`, !!r);
  if (!m) { truthy(`${p.id}: correctly excluded`, r.excluded === true); continue; }
  if (!p.price) {
    truthy(`${p.id}: unpriced, so not ranked`, r.rank === null || r.rank === undefined);
    truthy(`${p.id}: unpriced, so coverage < 100%`, r.score_coverage < 0.999);
    continue;
  }

  modelled++;
  const price = p.price;
  const taxRate = A.tax_rates[m.tax_key];
  const ins = A.insurance_annual[m.ins_key];
  const hoa = A.hoa_annual[m.hoa_key];
  const rent = m.rent_estimate;

  eq(`${p.id}: tax rate wired`, r.tax_rate, taxRate, 1e-12);
  eq(`${p.id}: insurance wired`, r.insurance, ins, 0);
  eq(`${p.id}: hoa wired`, r.hoa, hoa, 0);
  eq(`${p.id}: rent wired`, r.rent, rent, 0);

  const down = price * fin.down_payment_pct;
  const loan = price - down;
  eq(`${p.id}: down payment`, r.down, Math.round(down), 1);
  eq(`${p.id}: loan`, r.loan, Math.round(loan), 1);
  eq(`${p.id}: cash in`, r.cash_in,
    Math.round(down + price * fin.closing_costs_pct), 1);

  for (const [tag, rate] of [["base", fin.rate_base],
                             ["low", fin.rate_low],
                             ["high", fin.rate_high]]) {
    eq(`${p.id}: P&I ${tag}`, r[`pi_${tag}`],
      Math.round(monthlyPayment(loan, rate, fin.term_years)), 1);
  }

  const taxM = (price * taxRate) / 12;
  const insM = ins / 12;
  const hoaM = hoa / 12;
  eq(`${p.id}: tax/mo`, r.tax_month, Math.round(taxM), 1);
  eq(`${p.id}: ins/mo`, r.ins_month, Math.round(insM), 1);
  eq(`${p.id}: hoa/mo`, r.hoa_month, Math.round(hoaM), 1);

  const leak = op.vacancy_pct + op.maintenance_capex_pct + op.management_pct;
  eq(`${p.id}: leakage total`, r.leak_pct, leak, 1e-12);
  const egi = rent * (1 - leak);
  eq(`${p.id}: effective income/mo`, r.egi_month, Math.round(egi), 1);

  const noi = egi * 12 - price * taxRate - ins - hoa;
  eq(`${p.id}: NOI/yr`, r.noi_year, Math.round(noi), 1);
  eq(`${p.id}: cap rate`, r.cap_rate, Math.round((noi / price) * 1e4) / 1e4, 1e-9);

  for (const tag of ["base", "low", "high"]) {
    const cf = egi - r[`pi_${tag}`] - taxM - insM - hoaM;
    eq(`${p.id}: cash flow ${tag}`, r[`cf_${tag}`], Math.round(cf), 1);
    eq(`${p.id}: cash flow ${tag} annual`, r[`cf_${tag}_year`],
      Math.round(Math.round(cf) * 12), 12);
  }

  eq(`${p.id}: DSCR`, r.dscr,
    Math.round((noi / (r.pi_base * 12)) * 1e3) / 1e3, 1e-9);

  // Break-even rent must, by construction, produce zero cash flow.
  const be = r.breakeven_rent;
  const cfAtBreakeven = be * (1 - leak) - r.pi_base - taxM - insM - hoaM;
  truthy(`${p.id}: break-even rent really breaks even ` +
    `(residual ${cfAtBreakeven.toFixed(2)})`, Math.abs(cfAtBreakeven) < 1.5);

  eq(`${p.id}: 1% rule target`, r.one_pct_rent_needed, Math.round(price * 0.01), 1);

  // --- directional invariants that must hold for the report's thesis ---
  truthy(`${p.id}: cap rate below debt cost (negative leverage)`,
    r.cap_rate < fin.rate_base);
  truthy(`${p.id}: cash flow negative`, r.cf_base < 0);
  truthy(`${p.id}: DSCR below 1.0`, r.dscr < 1.0);
  truthy(`${p.id}: lower rate improves cash flow`, r.cf_low > r.cf_high);
  truthy(`${p.id}: rent below break-even`, rent < r.breakeven_rent);
  truthy(`${p.id}: fails the 1% rule`, rent < price * 0.01);
}

// --- set-level checks ---
truthy(`five properties were modelled (got ${modelled})`, modelled === 5);
truthy("ranked set contains only fully-covered properties",
  results.ranked_ids.every((id) => byId[id].score_coverage >= 0.999));
truthy("unrankable set contains only partially-covered properties",
  results.unrankable_ids.every((id) => byId[id].score_coverage < 0.999));
truthy("ranks are dense and ordered from 1",
  results.ranked_ids.every((id, i) => byId[id].rank === i + 1));
truthy("ranking is monotonically decreasing in score",
  results.ranked_ids.every((id, i, a) =>
    i === 0 || byId[a[i - 1]].score >= byId[id].score));
truthy("every weight is positive",
  Object.values(results.weights).every((w) => w > 0));
eq("weights sum as published", results.weight_total,
  Object.values(results.weights).reduce((a, b) => a + b, 0), 1e-9);
eq("financial weight as published", results.financial_weight,
  results.weights.cashflow + results.weights.yield + results.weights.price_value,
  1e-9);

// The headline claim of the report.
truthy("EVERY priced property is cash-flow negative",
  results.ranked_ids.every((id) => byId[id].cf_base < 0));
truthy("EVERY priced property has a cap rate under the mortgage rate",
  results.ranked_ids.every((id) => byId[id].cap_rate < fin.rate_base));

// Inventory reconciliation must actually add up.
const rec = props.inventory_reconciliation;
eq("inventory: 14 images - 1 dup - 1 unidentified = 12",
  rec.images_supplied - rec.duplicate_images - rec.unidentified_images,
  rec.unique_identified_properties, 0);
eq("inventory: price confidence buckets sum to 12",
  rec.with_confirmed_exact_price + rec.with_derived_price +
  rec.with_range_only + rec.with_no_price,
  rec.unique_identified_properties, 0);
eq("inventory: bedroom buckets sum to 12",
  rec.confirmed_5_bedroom + rec.confirmed_not_5_bedroom +
  rec.bedroom_count_unknown,
  rec.unique_identified_properties, 0);
eq("inventory: properties array holds 12 identified + 1 unidentified",
  props.properties.length, rec.unique_identified_properties + 1, 0);

console.log(`\n  ${pass} assertions passed`);
if (fails.length) {
  console.log(`  ${fails.length} FAILED:`);
  for (const f of fails) console.log(`    - ${f}`);
  process.exit(1);
}
console.log("  independent re-derivation agrees with results.json");
