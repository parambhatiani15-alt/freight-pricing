-- 003_rls.sql
-- Run AFTER 001_schema.sql and 002_seed.sql.
--
-- Locks every table down to read-only for the public (anon) role. The
-- dashboard only ever reads, so this changes nothing functionally — it just
-- stops anyone with the (public-by-design) anon key from inserting, updating,
-- or deleting the illustrative data.

alter table carriers                        enable row level security;
alter table lanes                           enable row level security;
alter table service_levels                  enable row level security;
alter table carrier_rates                   enable row level security;
alter table fuel_levy_index                 enable row level security;
alter table accessorials                    enable row level security;
alter table customers                       enable row level security;
alter table customer_rate_cards             enable row level security;
alter table shipments                       enable row level security;
alter table quotes                          enable row level security;
alter table monthly_account_margin_summary  enable row level security;

-- With RLS enabled and no insert/update/delete policies, writes are denied by
-- default. These policies grant public read access only. Each is dropped
-- first so the script is safe to re-run.
drop policy if exists "public read" on carriers;
drop policy if exists "public read" on lanes;
drop policy if exists "public read" on service_levels;
drop policy if exists "public read" on carrier_rates;
drop policy if exists "public read" on fuel_levy_index;
drop policy if exists "public read" on accessorials;
drop policy if exists "public read" on customers;
drop policy if exists "public read" on customer_rate_cards;
drop policy if exists "public read" on shipments;
drop policy if exists "public read" on quotes;
drop policy if exists "public read" on monthly_account_margin_summary;

create policy "public read" on carriers                        for select using (true);
create policy "public read" on lanes                           for select using (true);
create policy "public read" on service_levels                  for select using (true);
create policy "public read" on carrier_rates                   for select using (true);
create policy "public read" on fuel_levy_index                 for select using (true);
create policy "public read" on accessorials                    for select using (true);
create policy "public read" on customers                       for select using (true);
create policy "public read" on customer_rate_cards             for select using (true);
create policy "public read" on shipments                       for select using (true);
create policy "public read" on quotes                          for select using (true);
create policy "public read" on monthly_account_margin_summary  for select using (true);
