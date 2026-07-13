# Freight Pricing & Margin Monitor

A portfolio project for 4PL / freight pricing analyst roles (built with EFM Logistics,
Team Global Express, and similar Melbourne-based 4PL/transport roles in mind). It does
two things a pricing analyst actually does:

1. **Quotes a lane** — chargeable weight, live fuel levy, accessorials, carrier selection,
   and a full margin waterfall against either an existing customer's fixed rate card or a
   default markup for a new prospect.
2. **Monitors margin over time** — tracks realized margin against target for every account,
   month by month, and flags accounts that have drifted, with a lightweight root-cause hint
   (mix shift toward accessorial-heavy freight vs. a carrier rate change that outran the
   rate card).

**Live pieces:** Python calculation engine → Supabase (Postgres) → Next.js dashboard on
Vercel. Swap the seed data for real numbers and the dashboard keeps working unchanged.

---

## Honesty audit — read this before using it in an interview

**All data is synthetic.** Twelve fictional customers, six fictional carriers, twelve
Australian lanes (real distances, fictional rates), and ~4,900 generated shipments over
~19 months. Nothing here is EFM's, TGE's, or anyone else's real pricing data. Say so
plainly if asked — the value of this project is the *mechanic*, not the numbers.

**The margin-erosion stories are deliberately engineered, not organic.** Three accounts
were built with specific patterns so the monitoring layer has something real to catch:
- `CUST01` (Bendigo FoodWorks) — stable control, margin holds near target throughout.
- `CUST02` (Southern Ranges Retail) — mix-shift erosion: increasingly ships
  accessorial-heavy freight (which is passed through at a thinner margin than base
  linehaul) without a rate card correction. Chronic, noisy, never fully resolved in the
  data — deliberately left as the "still needs attention" case.
- `CUST03` (Cascade Building Supplies) — a carrier rate increase on their dominant lane
  (Melbourne–Perth, 2025-07-01) erodes margin sharply for two months, then a rate card
  correction (2025-09-01) recovers it. This is the complete quote → monitor → catch →
  reprice loop.

Everyone else gets realistic noise around their target margin. If you present this,
be upfront that the *dataset* was designed to demonstrate the mechanic — the *mechanic
itself* (fixed rate cards drifting from live costs) is real and is exactly how margin
erosion happens in practice.

**Modelling assumptions, stated explicitly (see `engine/pricing_engine.py` docstring for
the full list):**
- Chargeable weight = `max(actual kg, volume_m3 × 250)`. 250 kg/m³ is an illustrative
  AU road-freight cubic conversion factor; real factors vary by carrier and mode.
- Fuel levy is modelled as a live, symmetric pass-through on both buy and sell sides
  (matches common industry practice) — so fuel movement alone doesn't erode margin in
  this model. Real contracts vary; some lock a fuel levy for a period, which would
  reintroduce fuel risk on top of what's modelled here.
- Accessorials are passed through at cost + a flat 10% handling fee (thinner than the
  ~15–30% base linehaul markup) — this is what makes accessorial-heavy mix shift erode
  blended margin even when the base rate card is technically fine.
- The quote calculator's carrier selection picks the cheapest *eligible* carrier for the
  lane/service/weight — a lightweight optimization, not a constrained multi-lane RFP/tender
  allocation (that would be a different, larger project).
- Target margin in the monitoring table is volume-weighted by the customer's *actual*
  shipment mix that month, not a flat average across their whole rate card book — otherwise
  a correction on a customer's dominant lane gets diluted into invisibility by their many
  rarely-used lanes.

**Known limitation:** the live Quote Calculator's pricing logic is duplicated in two
languages — Python (`engine/pricing_engine.py`, the audited source of truth that generated
and validated the dataset) and TypeScript (`dashboard/lib/pricingEngine.ts`, used for
in-browser responsiveness). They're kept in sync by design and spot-checked against the
same test scenarios, but a single source of truth (e.g. a small pricing API) would be the
more defensible architecture for anything beyond a portfolio piece — worth naming as a
"if I had more time" in an interview.

---

## Architecture

```
scripts/01_generate_reference_data.py   → carriers, lanes, rates, fuel index, customers, rate cards
scripts/02_generate_shipments.py        → ~19 months of synthetic shipment history
engine/pricing_engine.py                → the calculation engine (quoting + margin monitoring)
scripts/03_build_kpi_tables.py          → runs the engine, builds monthly_account_margin_summary
scripts/04_build_seed_sql.py            → bundles everything into schema/002_seed.sql
schema/001_schema.sql                   → Postgres schema (apply first)
schema/002_seed.sql                     → seed data (apply second)
dashboard/                              → Next.js app (Quote Calculator + Portfolio Health)
```

The Python engine is the audited source of truth: it's what generated the historical
data and what you'd point to as "here's the tested calculation logic." The pre-aggregated
`monthly_account_margin_summary` table means the dashboard doesn't need to recompute
margin trends on every page load — same pattern as the KPI layer in the inventory project.

**To swap in real data:** replace the CSVs under `data/` with real exports (same column
shapes), or write directly into the Supabase tables — the dashboard reads live from
Supabase and doesn't care where the rows came from.

---

## Setup

### 1. Regenerate the data (optional — CSVs and seed SQL are already built)

```bash
cd freight-pricing
pip install pandas numpy --break-system-packages
python3 scripts/01_generate_reference_data.py
python3 scripts/02_generate_shipments.py
python3 scripts/03_build_kpi_tables.py
python3 scripts/04_build_seed_sql.py
```

### 2. Supabase

1. Create a project at supabase.com (or use your existing one).
2. Open the SQL editor and run `schema/001_schema.sql`, then `schema/002_seed.sql`
   (the seed file is large — ~720KB — the SQL editor handles it fine, or use
   `psql "$SUPABASE_DB_URL" -f schema/001_schema.sql` / `-f schema/002_seed.sql` if you
   prefer the CLI).
3. Grab your Project URL and `anon` public key from Project Settings → API.

### 3. Dashboard

```bash
cd dashboard
npm install
cp .env.local.example .env.local   # then fill in your Supabase URL + anon key
npm run dev                         # http://localhost:3000
```

### 4. Deploy to Vercel

```bash
npm i -g vercel     # if you don't have it
cd dashboard
vercel               # follow the prompts, link/create a project
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel --prod
```

(Or connect the `dashboard/` folder to a GitHub repo and import it in the Vercel
dashboard — same env vars, either way works.)

---

## What this demonstrates (for your CV / cover letter)

Mapped back to the Phase 1 research on what Melbourne 4PL pricing analyst roles actually
screen for:

- **Buy rate vs. sell rate margin management** — the core mechanic of the whole project.
- **Rate cards, weight breaks, fuel levy, accessorials** — modelled explicitly, not
  abstracted away.
- **RFP/tender vocabulary and cost-to-serve thinking** — the monitoring layer's root-cause
  hints are exactly the kind of analysis that feeds a rate review conversation.
- **SQL / data modelling** — a normalized schema (carriers, lanes, rate cards, shipments)
  built and queried, not a flat spreadsheet.
- **Python + dashboarding stack** — matches the tool stack these roles actually list
  (Excel/SQL/Power BI equivalents), built end-to-end and deployed, not a notebook.
