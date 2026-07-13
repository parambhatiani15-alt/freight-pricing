"""
Generates the reference (non-transactional) data for the freight pricing project:
carriers, lanes, service_levels, carrier_rates, fuel_levy_index, accessorials,
customers, customer_rate_cards.

All data is SYNTHETIC / ILLUSTRATIVE. Carrier and customer names are fictional.
Lane distances are real-world approximate road distances between AU capitals/
regional centres (a factual, non-copyrighted geographic detail) used to make
rate-per-km sanity checks realistic.
"""
import numpy as np
import pandas as pd
from datetime import date

rng = np.random.default_rng(42)

OUT = "/home/claude/freight-pricing/data"

# ---------------------------------------------------------------------------
# Carriers (fictional names — avoids implying any real carrier's actual rates)
# ---------------------------------------------------------------------------
carriers = pd.DataFrame([
    dict(carrier_id="CAR01", carrier_name="Austral Roadlink",      mode="road",        on_time_pct=96.5, tender_accept_pct=97.0, damage_rate_pct=0.18, notes="Primary metro/interstate road carrier"),
    dict(carrier_id="CAR02", carrier_name="Southern Cross Freight", mode="road",        on_time_pct=94.0, tender_accept_pct=93.5, damage_rate_pct=0.31, notes="Competitive on regional lanes"),
    dict(carrier_id="CAR03", carrier_name="Interstate Rail Co",     mode="intermodal",  on_time_pct=91.0, tender_accept_pct=99.0, damage_rate_pct=0.12, notes="Best cost on long-haul interstate, slower transit"),
    dict(carrier_id="CAR04", carrier_name="QuickHaul Express",      mode="road",        on_time_pct=98.0, tender_accept_pct=95.0, damage_rate_pct=0.22, notes="Premium express, higher cost"),
    dict(carrier_id="CAR05", carrier_name="Outback Carriers",       mode="road",        on_time_pct=89.5, tender_accept_pct=90.0, damage_rate_pct=0.40, notes="Best coverage for remote/regional"),
    dict(carrier_id="CAR06", carrier_name="Metro Cartage Co",       mode="road",        on_time_pct=97.2, tender_accept_pct=96.0, damage_rate_pct=0.15, notes="Metro cartage specialist, not competitive interstate"),
])

# ---------------------------------------------------------------------------
# Lanes (approx real road distances — illustrative, rounded)
# ---------------------------------------------------------------------------
lanes = pd.DataFrame([
    dict(lane_id="L01", origin_city="Melbourne", origin_state="VIC", dest_city="Sydney",    dest_state="NSW", distance_km=880,  lane_type="interstate"),
    dict(lane_id="L02", origin_city="Melbourne", origin_state="VIC", dest_city="Brisbane",   dest_state="QLD", distance_km=1675, lane_type="interstate"),
    dict(lane_id="L03", origin_city="Melbourne", origin_state="VIC", dest_city="Adelaide",   dest_state="SA",  distance_km=730,  lane_type="interstate"),
    dict(lane_id="L04", origin_city="Melbourne", origin_state="VIC", dest_city="Perth",      dest_state="WA",  distance_km=3420, lane_type="interstate"),
    dict(lane_id="L05", origin_city="Sydney",    origin_state="NSW", dest_city="Brisbane",   dest_state="QLD", distance_km=920,  lane_type="interstate"),
    dict(lane_id="L06", origin_city="Melbourne", origin_state="VIC", dest_city="Geelong",    dest_state="VIC", distance_km=75,   lane_type="metro"),
    dict(lane_id="L07", origin_city="Melbourne", origin_state="VIC", dest_city="Dandenong",  dest_state="VIC", distance_km=35,   lane_type="metro"),
    dict(lane_id="L08", origin_city="Melbourne", origin_state="VIC", dest_city="Mildura",    dest_state="VIC", distance_km=550,  lane_type="regional"),
    dict(lane_id="L09", origin_city="Melbourne", origin_state="VIC", dest_city="Bendigo",    dest_state="VIC", distance_km=150,  lane_type="regional"),
    dict(lane_id="L10", origin_city="Melbourne", origin_state="VIC", dest_city="Albury",     dest_state="NSW", distance_km=325,  lane_type="regional"),
    dict(lane_id="L11", origin_city="Melbourne", origin_state="VIC", dest_city="Darwin",     dest_state="NT",  distance_km=3750, lane_type="regional"),
    dict(lane_id="L12", origin_city="Sydney",    origin_state="NSW", dest_city="Perth",      dest_state="WA",  distance_km=4130, lane_type="interstate"),
])

# ---------------------------------------------------------------------------
# Service levels
# ---------------------------------------------------------------------------
service_levels = pd.DataFrame([
    dict(service_level_id="SVC_EXP", service_name="Express (Next Day)", target_transit_days=1.0),
    dict(service_level_id="SVC_STD", service_name="Standard",            target_transit_days=3.0),
    dict(service_level_id="SVC_ECO", service_name="Economy",             target_transit_days=6.0),
])

# ---------------------------------------------------------------------------
# Carrier rates: per carrier x lane x service level x weight break
# Base rate/kg scales with distance and tapers down for heavier weight breaks
# (standard freight rate-card shape). Not every carrier services every lane/
# service level (reflects real carrier network gaps).
# Two effective periods are modelled for CAR01 on lane L04 (Melbourne-Perth)
# to simulate a mid-year carrier rate increase — used later to demonstrate
# margin drift on an Enterprise account (Cascade Building Supplies).
# ---------------------------------------------------------------------------
WEIGHT_BREAKS = [(0, 25), (25, 100), (100, 500), (500, 3000), (3000, None)]

# base $/kg at the smallest weight break, per 100km, before taper — differs by carrier "positioning"
CARRIER_BASE_RATE_PER_100KM = {
    "CAR01": 4.20, "CAR02": 3.95, "CAR03": 3.40, "CAR04": 5.10, "CAR05": 4.60, "CAR06": 4.00,
}
SERVICE_MULTIPLIER = {"SVC_EXP": 1.35, "SVC_STD": 1.00, "SVC_ECO": 0.80}
TAPER = {  # multiplier applied per weight break relative to smallest break
    (0, 25): 1.00, (25, 100): 0.82, (100, 500): 0.64, (500, 3000): 0.48, (3000, None): 0.36,
}

# which carriers service which lanes (network reality — not universal coverage)
LANE_CARRIER_MAP = {
    "L01": ["CAR01", "CAR02", "CAR03", "CAR04"],
    "L02": ["CAR01", "CAR03", "CAR04"],
    "L03": ["CAR01", "CAR02", "CAR03"],
    "L04": ["CAR01", "CAR03"],
    "L05": ["CAR01", "CAR02", "CAR04"],
    "L06": ["CAR01", "CAR06", "CAR02"],
    "L07": ["CAR01", "CAR06", "CAR04"],
    "L08": ["CAR02", "CAR05"],
    "L09": ["CAR02", "CAR05", "CAR01"],
    "L10": ["CAR01", "CAR02", "CAR05"],
    "L11": ["CAR05", "CAR03"],
    "L12": ["CAR03", "CAR01"],
}
# which service levels each lane offers (long-haul/remote often skip Express)
LANE_SERVICE_MAP = {
    "L01": ["SVC_EXP", "SVC_STD", "SVC_ECO"], "L02": ["SVC_EXP", "SVC_STD", "SVC_ECO"],
    "L03": ["SVC_EXP", "SVC_STD", "SVC_ECO"], "L04": ["SVC_STD", "SVC_ECO"],
    "L05": ["SVC_EXP", "SVC_STD", "SVC_ECO"], "L06": ["SVC_EXP", "SVC_STD"],
    "L07": ["SVC_EXP", "SVC_STD"], "L08": ["SVC_STD", "SVC_ECO"],
    "L09": ["SVC_EXP", "SVC_STD", "SVC_ECO"], "L10": ["SVC_STD", "SVC_ECO"],
    "L11": ["SVC_ECO"], "L12": ["SVC_STD", "SVC_ECO"],
}

lane_dist = dict(zip(lanes.lane_id, lanes.distance_km))

rate_rows = []
for lane_id, carrier_ids in LANE_CARRIER_MAP.items():
    dist = lane_dist[lane_id]
    for carrier_id in carrier_ids:
        base = CARRIER_BASE_RATE_PER_100KM[carrier_id] * (dist / 100)
        for svc in LANE_SERVICE_MAP[lane_id]:
            svc_mult = SERVICE_MULTIPLIER[svc]
            for (lo, hi) in WEIGHT_BREAKS:
                taper = TAPER[(lo, hi)]
                rate_per_kg = round(base * svc_mult * taper * 0.01 + 0.35, 4)  # scaled to sane $/kg
                min_charge = round(35 + dist * 0.01, 2)

                # Standard single-period rate for everything except the
                # CAR01 / L04 storyline lane, which gets a rate increase
                # partway through the shipment history (simulated below).
                if carrier_id == "CAR01" and lane_id == "L04":
                    rate_rows.append(dict(carrier_id=carrier_id, lane_id=lane_id, service_level_id=svc,
                                           weight_break_min_kg=lo, weight_break_max_kg=hi,
                                           rate_per_kg=rate_per_kg, min_charge=min_charge,
                                           effective_from=date(2024, 10, 1), effective_to=date(2025, 6, 30)))
                    rate_rows.append(dict(carrier_id=carrier_id, lane_id=lane_id, service_level_id=svc,
                                           weight_break_min_kg=lo, weight_break_max_kg=hi,
                                           rate_per_kg=round(rate_per_kg * 1.14, 4), min_charge=round(min_charge * 1.10, 2),
                                           effective_from=date(2025, 7, 1), effective_to=None))
                else:
                    rate_rows.append(dict(carrier_id=carrier_id, lane_id=lane_id, service_level_id=svc,
                                           weight_break_min_kg=lo, weight_break_max_kg=hi,
                                           rate_per_kg=rate_per_kg, min_charge=min_charge,
                                           effective_from=date(2024, 10, 1), effective_to=None))

carrier_rates = pd.DataFrame(rate_rows)
carrier_rates["effective_from"] = pd.to_datetime(carrier_rates["effective_from"])
carrier_rates["effective_to"] = pd.to_datetime(carrier_rates["effective_to"])

# ---------------------------------------------------------------------------
# Fuel levy index — monthly, trending up with noise (mirrors real volatility
# referenced in industry commentary on fuel surcharge movements)
# ---------------------------------------------------------------------------
months = pd.date_range("2024-10-01", "2026-06-01", freq="MS")
base_levy = np.linspace(19.5, 27.0, len(months))  # gradual upward trend
noise = rng.normal(0, 0.6, len(months))
levy_pct = np.round(np.clip(base_levy + noise, 15, 32), 2)
fuel_levy_index = pd.DataFrame({"month": months.date, "levy_pct": levy_pct})

# ---------------------------------------------------------------------------
# Accessorials
# ---------------------------------------------------------------------------
accessorials = pd.DataFrame([
    dict(accessorial_id="ACC_TAILLIFT", accessorial_name="Tail-lift delivery", charge_type="flat", amount=45.00),
    dict(accessorial_id="ACC_RESI",     accessorial_name="Residential delivery", charge_type="flat", amount=18.00),
    dict(accessorial_id="ACC_REMOTE",   accessorial_name="Remote area surcharge", charge_type="per_kg", amount=0.18),
    dict(accessorial_id="ACC_REDEL",    accessorial_name="Redelivery fee", charge_type="flat", amount=38.00),
    dict(accessorial_id="ACC_HAZMAT",   accessorial_name="Hazmat handling", charge_type="pct_of_linehaul", amount=8.00),
])

# ---------------------------------------------------------------------------
# Customers — includes three "storyline" accounts used later to demonstrate
# margin monitoring: one stable control, one mix-shift erosion, one carrier-
# rate-drift erosion that gets corrected mid-way through the history.
# ---------------------------------------------------------------------------
customers = pd.DataFrame([
    dict(customer_id="CUST01", customer_name="Bendigo FoodWorks Group",  segment="SME",        volume_tier="Low",    onboarded_date=date(2024, 10, 15)),
    dict(customer_id="CUST02", customer_name="Southern Ranges Retail",   segment="Mid-Market",  volume_tier="Medium", onboarded_date=date(2024, 10, 20)),
    dict(customer_id="CUST03", customer_name="Cascade Building Supplies",segment="Enterprise",  volume_tier="High",   onboarded_date=date(2024, 10, 5)),
    dict(customer_id="CUST04", customer_name="Yarra Valley Wines Co",    segment="SME",         volume_tier="Low",    onboarded_date=date(2024, 11, 1)),
    dict(customer_id="CUST05", customer_name="Bayside Furniture Direct", segment="Mid-Market",   volume_tier="Medium", onboarded_date=date(2024, 11, 10)),
    dict(customer_id="CUST06", customer_name="Northline Electrical Wholesale", segment="Mid-Market", volume_tier="Medium", onboarded_date=date(2024, 12, 1)),
    dict(customer_id="CUST07", customer_name="Peninsula Produce Co",     segment="SME",         volume_tier="Low",    onboarded_date=date(2025, 1, 15)),
    dict(customer_id="CUST08", customer_name="TitanFit Sporting Goods",  segment="Mid-Market",   volume_tier="Medium", onboarded_date=date(2025, 2, 1)),
    dict(customer_id="CUST09", customer_name="Alpine Outdoor Equipment", segment="SME",         volume_tier="Low",    onboarded_date=date(2025, 3, 10)),
    dict(customer_id="CUST10", customer_name="Redgum Timber & Hardware", segment="Enterprise",  volume_tier="High",   onboarded_date=date(2024, 10, 25)),
    dict(customer_id="CUST11", customer_name="Coastal Appliance Distributors", segment="Enterprise", volume_tier="High", onboarded_date=date(2025, 1, 5)),
    dict(customer_id="CUST12", customer_name="Metro Office Supplies",    segment="SME",         volume_tier="Low",    onboarded_date=date(2025, 4, 1)),
])

# ---------------------------------------------------------------------------
# Customer rate cards — markup over (buy cost + surcharges).
# Enterprise/High volume gets thinner markup, SME/Low gets fatter markup
# (standard commercial logic — the pricing analyst's actual lever).
# target_margin_pct is derived consistently: margin% = markup% / (1+markup%)
# CUST03 (Cascade) gets a rate-card update mid-2025 — simulating the pricing
# analyst catching the carrier rate increase on L04 and correcting the sell
# side. CUST02 (Southern Ranges) does NOT get corrected — it stays "at risk"
# through to the end of the data, which is the point: the dashboard should
# surface it as unresolved.
# ---------------------------------------------------------------------------
SEGMENT_MARKUP = {
    ("SME", "Low"): 0.30,
    ("Mid-Market", "Medium"): 0.22,
    ("Enterprise", "High"): 0.15,
}

def markup_to_margin(markup):
    return round(100 * markup / (1 + markup), 3)

# ---------------------------------------------------------------------------
# Reference buy rate: the "typical shipment" (100-500kg weight break) linehaul
# $/kg used as the basis for setting a customer's fixed sell rate at the time
# a rate card is created. This is deliberately NOT recalculated on every
# shipment -- a real commercial rate card is a fixed number until someone
# actively repriced it, which is exactly the mechanic that makes margin
# erosion possible to demonstrate.
# ---------------------------------------------------------------------------
def reference_buy_rate(lane_id, service_level_id, weight_break, as_of, carrier_id=None):
    as_of = pd.Timestamp(as_of)
    lo, hi = weight_break
    pool = carrier_rates[
        (carrier_rates.lane_id == lane_id) &
        (carrier_rates.service_level_id == service_level_id) &
        (carrier_rates.weight_break_min_kg == lo) &
        (carrier_rates.effective_from <= as_of) &
        ((carrier_rates.effective_to.isna()) | (carrier_rates.effective_to >= as_of))
    ]
    if carrier_id is not None:
        pool = pool[pool.carrier_id == carrier_id]
    if pool.empty:
        return None, None
    return float(pool.rate_per_kg.mean()), float(pool.min_charge.mean())

# Customer rate cards are keyed on the SPECIFIC lane (not a lane-type bucket)
# and mirror the same weight-break tiers as carrier_rates. Both choices exist
# to eliminate structural pricing noise: a blended lane-type rate would
# misprice lanes of very different distance, and a flat (non-tiered) rate
# would misprice small vs. large shipments -- either would drown out the
# genuine erosion stories this dataset is built to demonstrate.
rate_card_rows = []
for _, c in customers.iterrows():
    markup = SEGMENT_MARKUP[(c.segment, c.volume_tier)]
    for _, lane in lanes.iterrows():
        lane_id = lane.lane_id
        services_on_lane = carrier_rates[carrier_rates.lane_id == lane_id].service_level_id.unique()
        for svc in services_on_lane:
            for (lo, hi) in WEIGHT_BREAKS:
                if c.customer_id == "CUST03" and lane_id == "L04":
                    # Rate card set against CAR01 specifically (their dominant
                    # carrier on this lane) so the mid-2025 carrier rate
                    # increase shows up clearly, then gets corrected once the
                    # analyst catches it.
                    ref_rate, ref_min = reference_buy_rate(lane_id, svc, (lo, hi), date(2024, 10, 1), carrier_id="CAR01")
                    if ref_rate is None:
                        continue
                    sell_rate = round(ref_rate * (1 + markup), 4)
                    sell_min = round(ref_min * (1 + markup), 2)
                    rate_card_rows.append(dict(customer_id=c.customer_id, lane_id=lane_id, service_level_id=svc,
                                                weight_break_min_kg=lo, weight_break_max_kg=hi,
                                                sell_rate_per_kg=sell_rate, sell_min_charge=sell_min,
                                                markup_pct=round(markup * 100, 2), target_margin_pct=markup_to_margin(markup),
                                                effective_from=date(2024, 10, 1), effective_to=date(2025, 8, 31)))
                    corrected_markup = markup + 0.06  # analyst repriced up ~6pts after catching the drift
                    ref_rate2, ref_min2 = reference_buy_rate(lane_id, svc, (lo, hi), date(2025, 9, 1), carrier_id="CAR01")
                    sell_rate2 = round(ref_rate2 * (1 + corrected_markup), 4)
                    sell_min2 = round(ref_min2 * (1 + corrected_markup), 2)
                    rate_card_rows.append(dict(customer_id=c.customer_id, lane_id=lane_id, service_level_id=svc,
                                                weight_break_min_kg=lo, weight_break_max_kg=hi,
                                                sell_rate_per_kg=sell_rate2, sell_min_charge=sell_min2,
                                                markup_pct=round(corrected_markup * 100, 2), target_margin_pct=markup_to_margin(corrected_markup),
                                                effective_from=date(2025, 9, 1), effective_to=None))
                else:
                    ref_rate, ref_min = reference_buy_rate(lane_id, svc, (lo, hi), date(2024, 10, 1))
                    if ref_rate is None:
                        continue
                    sell_rate = round(ref_rate * (1 + markup), 4)
                    sell_min = round(ref_min * (1 + markup), 2)
                    rate_card_rows.append(dict(customer_id=c.customer_id, lane_id=lane_id, service_level_id=svc,
                                                weight_break_min_kg=lo, weight_break_max_kg=hi,
                                                sell_rate_per_kg=sell_rate, sell_min_charge=sell_min,
                                                markup_pct=round(markup * 100, 2), target_margin_pct=markup_to_margin(markup),
                                                effective_from=date(2024, 10, 1), effective_to=None))

customer_rate_cards = pd.DataFrame(rate_card_rows)

# ---------------------------------------------------------------------------
# Write everything out
# ---------------------------------------------------------------------------
carriers.to_csv(f"{OUT}/carriers.csv", index=False)
lanes.to_csv(f"{OUT}/lanes.csv", index=False)
service_levels.to_csv(f"{OUT}/service_levels.csv", index=False)
carrier_rates.to_csv(f"{OUT}/carrier_rates.csv", index=False)
fuel_levy_index.to_csv(f"{OUT}/fuel_levy_index.csv", index=False)
accessorials.to_csv(f"{OUT}/accessorials.csv", index=False)
customers.to_csv(f"{OUT}/customers.csv", index=False)
customer_rate_cards.to_csv(f"{OUT}/customer_rate_cards.csv", index=False)

print("Reference data generated:")
for name, df in [("carriers", carriers), ("lanes", lanes), ("service_levels", service_levels),
                  ("carrier_rates", carrier_rates), ("fuel_levy_index", fuel_levy_index),
                  ("accessorials", accessorials), ("customers", customers),
                  ("customer_rate_cards", customer_rate_cards)]:
    print(f"  {name}: {len(df)} rows")
