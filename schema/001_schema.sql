-- ============================================================================
-- Freight Pricing & Margin Monitoring — Schema
-- Illustrative 4PL pricing-analyst portfolio project.
-- All data loaded against this schema is SYNTHETIC / ILLUSTRATIVE.
-- ============================================================================

-- ---------- Network reference data ----------

create table if not exists carriers (
    carrier_id      text primary key,
    carrier_name    text not null,
    mode            text not null check (mode in ('road','intermodal')),
    on_time_pct     numeric(5,2) not null,       -- illustrative service KPI
    tender_accept_pct numeric(5,2) not null,     -- % of tendered loads accepted
    damage_rate_pct numeric(5,3) not null,       -- % of shipments with a damage claim
    notes           text
);

create table if not exists lanes (
    lane_id         text primary key,
    origin_city     text not null,
    origin_state    text not null,
    dest_city       text not null,
    dest_state      text not null,
    distance_km     integer not null,
    lane_type       text not null check (lane_type in ('metro','interstate','regional'))
);

create table if not exists service_levels (
    service_level_id text primary key,
    service_name      text not null,
    target_transit_days numeric(4,1) not null
);

-- ---------- Buy-side: what we pay carriers ----------

create table if not exists carrier_rates (
    rate_id         bigint generated always as identity primary key,
    carrier_id      text not null references carriers(carrier_id),
    lane_id         text not null references lanes(lane_id),
    service_level_id text not null references service_levels(service_level_id),
    weight_break_min_kg numeric(10,2) not null,
    weight_break_max_kg numeric(10,2),            -- null = uncapped (top tier)
    rate_per_kg     numeric(10,4) not null,
    min_charge      numeric(10,2) not null,
    effective_from  date not null,
    effective_to    date                          -- null = currently active
);

create table if not exists fuel_levy_index (
    month           date primary key,             -- first of month
    levy_pct        numeric(5,2) not null          -- e.g. 24.50 = 24.5%
);

create table if not exists accessorials (
    accessorial_id  text primary key,
    accessorial_name text not null,
    charge_type     text not null check (charge_type in ('flat','per_kg','pct_of_linehaul')),
    amount          numeric(10,4) not null
);

-- ---------- Sell-side: what we charge customers ----------

create table if not exists customers (
    customer_id     text primary key,
    customer_name   text not null,
    segment         text not null check (segment in ('SME','Mid-Market','Enterprise')),
    volume_tier     text not null check (volume_tier in ('Low','Medium','High')),
    onboarded_date  date not null
);

create table if not exists customer_rate_cards (
    rate_card_id    bigint generated always as identity primary key,
    customer_id     text not null references customers(customer_id),
    lane_id         text not null references lanes(lane_id),
    service_level_id text not null references service_levels(service_level_id),
    weight_break_min_kg numeric(10,2) not null,      -- mirrors carrier_rates weight tiering
    weight_break_max_kg numeric(10,2),               -- null = uncapped (top tier)
    sell_rate_per_kg numeric(10,4) not null,        -- FIXED linehaul $/kg, locked at effective_from
    sell_min_charge numeric(10,2) not null,          -- FIXED minimum charge, locked at effective_from
    markup_pct      numeric(6,3) not null,          -- markup assumed over the reference buy cost when this rate was set
    target_margin_pct numeric(6,3) not null,        -- the margin this account is supposed to hold
    effective_from  date not null,
    effective_to    date
);
-- Note on design: sell_rate_per_kg is fixed for the life of the rate card
-- period (it is NOT recalculated against the carrier's current buy rate on
-- every shipment). This is deliberate: it's what makes margin erosion
-- possible to model at all. Fuel levy is applied symmetrically to both buy
-- and sell linehaul as a live pass-through (matching how fuel levies are
-- typically contracted in the industry), so fuel movement alone does not
-- erode margin -- erosion instead comes from carrier base-rate drift and
-- from a shift in shipment mix toward accessorial-heavy freight (which is
-- passed through at a thinner margin than the base linehaul rate).
-- Rate cards are keyed on the specific lane (not a broad lane-type bucket)
-- because our lane network spans ~35km metro hops to ~4,100km interstate
-- runs -- a single blended rate per category would misprice both ends.

-- ---------- Transactions ----------

create table if not exists shipments (
    shipment_id     bigint generated always as identity primary key,
    ship_date       date not null,
    customer_id     text not null references customers(customer_id),
    lane_id         text not null references lanes(lane_id),
    service_level_id text not null references service_levels(service_level_id),
    carrier_id      text not null references carriers(carrier_id),
    actual_weight_kg numeric(10,2) not null,
    volume_m3       numeric(10,3) not null,
    chargeable_weight_kg numeric(10,2) not null,
    accessorials_applied text[],                    -- array of accessorial_id
    buy_cost        numeric(10,2) not null,          -- what we paid the carrier (incl. surcharges)
    sell_price      numeric(10,2) not null,          -- what we billed the customer
    margin_pct      numeric(6,3) not null
);

create table if not exists quotes (
    quote_id        bigint generated always as identity primary key,
    created_at      timestamptz not null default now(),
    customer_id     text references customers(customer_id),  -- null = prospect / ad hoc
    prospect_name   text,
    lane_id         text not null references lanes(lane_id),
    service_level_id text not null references service_levels(service_level_id),
    actual_weight_kg numeric(10,2) not null,
    volume_m3       numeric(10,3) not null,
    chargeable_weight_kg numeric(10,2) not null,
    carrier_id      text references carriers(carrier_id),
    buy_cost        numeric(10,2) not null,
    surcharge_total numeric(10,2) not null,
    sell_price      numeric(10,2) not null,
    margin_pct      numeric(6,3) not null,
    margin_flag     text not null check (margin_flag in ('ok','warning','breach'))
);

-- Helpful indexes for the dashboard's typical query patterns
create index if not exists idx_shipments_customer_date on shipments(customer_id, ship_date);
create index if not exists idx_shipments_lane on shipments(lane_id);
create index if not exists idx_carrier_rates_lookup on carrier_rates(lane_id, service_level_id, carrier_id);
create index if not exists idx_quotes_created on quotes(created_at desc);
