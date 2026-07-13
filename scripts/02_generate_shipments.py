"""
Generates ~18 months of synthetic shipment transaction history.

Three deliberate storylines are built in so the margin-monitoring layer has
real patterns to detect (this is the whole point of the portfolio piece —
a flat, noise-only dataset wouldn't demonstrate anything):

  CUST01 (Bendigo FoodWorks)      — STABLE control account, margin holds near target.
  CUST02 (Southern Ranges Retail) — MIX-SHIFT erosion: increasingly ships to
                                     regional/remote lanes with more accessorials
                                     over time, but its rate card is never
                                     corrected. Stays "at risk" through to the
                                     end of the data — the unresolved case the
                                     dashboard should flag as needing action.
  CUST03 (Cascade Building Supplies) — CARRIER RATE DRIFT: its primary lane's
                                     carrier rate increases from 2025-07-01
                                     (see 01_generate_reference_data.py), margin
                                     erodes for two months, then the customer
                                     rate card is corrected 2025-09-01 and
                                     margin recovers. Demonstrates the full
                                     quote -> monitor -> catch -> reprice loop.

All other customers get realistic noise around their target margin.

Chargeable weight uses the standard AU road-freight cubic conversion of
250 kg per m3 (i.e. chargeable weight = max(actual kg, volume_m3 * 250)).
This is a common illustrative convention — real cubic factors vary by
carrier and mode (some use 333 kg/m3 for air) — documented in the README.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(7)
OUT = "/home/claude/freight-pricing/data"

carriers = pd.read_csv(f"{OUT}/carriers.csv")
lanes = pd.read_csv(f"{OUT}/lanes.csv")
carrier_rates = pd.read_csv(f"{OUT}/carrier_rates.csv", parse_dates=["effective_from", "effective_to"])
fuel_levy = pd.read_csv(f"{OUT}/fuel_levy_index.csv", parse_dates=["month"])
accessorials = pd.read_csv(f"{OUT}/accessorials.csv")
customers = pd.read_csv(f"{OUT}/customers.csv", parse_dates=["onboarded_date"])
rate_cards = pd.read_csv(f"{OUT}/customer_rate_cards.csv", parse_dates=["effective_from", "effective_to"])

CUBIC_FACTOR = 250  # kg per m3, illustrative AU road freight convention

lane_type_map = dict(zip(lanes.lane_id, lanes.lane_type))
lanes_by_type = lanes.groupby("lane_type")["lane_id"].apply(list).to_dict()

# monthly shipment volume by customer volume tier
VOLUME_TIER_SHIPMENTS_PER_MONTH = {"Low": (6, 12), "Medium": (15, 28), "High": (35, 60)}

# each customer has a "home" lane-type mix that can drift over time for the
# mix-shift storyline customer
DEFAULT_LANE_MIX = {"metro": 0.35, "interstate": 0.45, "regional": 0.20}
MIX_SHIFT_END_MIX = {"metro": 0.15, "interstate": 0.30, "regional": 0.55}  # CUST02 drifts here

MONTHS = pd.date_range("2024-10-01", "2026-06-01", freq="MS")


def get_active_rate(carrier_id, lane_id, service_level_id, weight_kg, ship_date):
    ship_date = pd.Timestamp(ship_date)
    subset = carrier_rates[
        (carrier_rates.carrier_id == carrier_id) &
        (carrier_rates.lane_id == lane_id) &
        (carrier_rates.service_level_id == service_level_id) &
        (carrier_rates.effective_from <= ship_date) &
        ((carrier_rates.effective_to.isna()) | (carrier_rates.effective_to >= ship_date)) &
        (carrier_rates.weight_break_min_kg <= weight_kg) &
        ((carrier_rates.weight_break_max_kg.isna()) | (carrier_rates.weight_break_max_kg > weight_kg))
    ]
    if subset.empty:
        return None
    return subset.iloc[0]


def get_active_rate_card(customer_id, lane_id, service_level_id, weight_kg, ship_date):
    ship_date = pd.Timestamp(ship_date)
    subset = rate_cards[
        (rate_cards.customer_id == customer_id) &
        (rate_cards.lane_id == lane_id) &
        (rate_cards.service_level_id == service_level_id) &
        (rate_cards.weight_break_min_kg <= weight_kg) &
        ((rate_cards.weight_break_max_kg.isna()) | (rate_cards.weight_break_max_kg > weight_kg)) &
        (rate_cards.effective_from <= ship_date) &
        ((rate_cards.effective_to.isna()) | (rate_cards.effective_to >= ship_date))
    ]
    return subset.iloc[0] if not subset.empty else None


def fuel_levy_for(ship_date):
    month_start = pd.Timestamp(ship_date.replace(day=1))
    row = fuel_levy[fuel_levy.month == month_start]
    return float(row.levy_pct.iloc[0]) if not row.empty else float(fuel_levy.levy_pct.mean())


CUST03_INTERSTATE_MIX = {"metro": 0.10, "interstate": 0.80, "regional": 0.10}


def pick_lane(customer_id, month_idx, n_months, storyline):
    if storyline == "mix_shift" and customer_id == "CUST02":
        # linearly interpolate the lane-type mix from default to the
        # regional/remote-heavy end state over the course of the data
        t = month_idx / max(n_months - 1, 1)
        mix = {k: DEFAULT_LANE_MIX[k] + t * (MIX_SHIFT_END_MIX[k] - DEFAULT_LANE_MIX[k]) for k in DEFAULT_LANE_MIX}
    elif storyline == "rate_drift" and customer_id == "CUST03":
        mix = CUST03_INTERSTATE_MIX
    else:
        mix = DEFAULT_LANE_MIX
    lane_types, probs = zip(*mix.items())
    probs = np.array(probs) / sum(probs)
    lane_type = rng.choice(lane_types, p=probs)

    if storyline == "rate_drift" and customer_id == "CUST03" and lane_type == "interstate" and rng.random() < 0.85:
        return "L04", "interstate"  # dominant lane for the rate-drift storyline

    candidates = lanes_by_type.get(lane_type, lanes_by_type["metro"])
    return rng.choice(candidates), lane_type


def pick_carrier_and_service(lane_id, lane_type, customer_id=None, storyline=None):
    eligible = carrier_rates[carrier_rates.lane_id == lane_id]
    if eligible.empty:
        return None, None
    if storyline == "rate_drift" and customer_id == "CUST03" and lane_id == "L04" and "CAR01" in eligible.carrier_id.values:
        carrier_id = "CAR01"  # keep the storyline lane's carrier consistent so the rate hike is visible
    else:
        carrier_id = rng.choice(eligible.carrier_id.unique())
    svc_options = eligible[eligible.carrier_id == carrier_id].service_level_id.unique()
    weights = {"SVC_EXP": 0.25, "SVC_STD": 0.55, "SVC_ECO": 0.20}
    probs = np.array([weights.get(s, 0.3) for s in svc_options])
    probs = probs / probs.sum()
    service_level_id = rng.choice(svc_options, p=probs)
    return carrier_id, service_level_id


def maybe_accessorials(lane_type, customer_id, month_idx, n_months, storyline):
    applied = []
    base_probs = {"ACC_TAILLIFT": 0.12, "ACC_RESI": 0.18, "ACC_REDEL": 0.05}
    if lane_type == "regional":
        base_probs["ACC_REMOTE"] = 0.35
    # mix-shift storyline: accessorial intensity ramps up alongside the lane drift
    if storyline == "mix_shift" and customer_id == "CUST02":
        t = month_idx / max(n_months - 1, 1)
        boost = 1 + t * 1.8
        base_probs = {k: min(v * boost, 0.85) for k, v in base_probs.items()}
    for acc_id, p in base_probs.items():
        if rng.random() < p:
            applied.append(acc_id)
    return applied


def accessorial_cost(applied, linehaul_cost, chargeable_weight_kg):
    total = 0.0
    for acc_id in applied:
        row = accessorials[accessorials.accessorial_id == acc_id].iloc[0]
        if row.charge_type == "flat":
            total += row.amount
        elif row.charge_type == "per_kg":
            total += row.amount * chargeable_weight_kg
        elif row.charge_type == "pct_of_linehaul":
            total += linehaul_cost * (row.amount / 100)
    return round(total, 2)


rows = []
n_months = len(MONTHS)

for _, cust in customers.iterrows():
    storyline = {"CUST02": "mix_shift", "CUST03": "rate_drift"}.get(cust.customer_id, "stable")
    lo, hi = VOLUME_TIER_SHIPMENTS_PER_MONTH[cust.volume_tier]

    for month_idx, month_start in enumerate(MONTHS):
        if pd.Timestamp(month_start) < pd.Timestamp(cust.onboarded_date.replace(day=1)):
            continue  # not yet a customer
        if pd.Timestamp(month_start) > pd.Timestamp("2026-05-01"):
            continue  # data ends May 2026 (current date context: July 2026)

        n_shipments = rng.integers(lo, hi + 1)
        for _ in range(n_shipments):
            day = rng.integers(1, 28)
            ship_date = date(month_start.year, month_start.month, day)

            lane_id, lane_type = pick_lane(cust.customer_id, month_idx, n_months, storyline)
            carrier_id, service_level_id = pick_carrier_and_service(lane_id, lane_type, cust.customer_id, storyline)
            if carrier_id is None:
                continue

            actual_weight = round(float(rng.gamma(3.0, 60)), 1)  # right-skewed, mostly 50-400kg
            volume_m3 = round(actual_weight / rng.uniform(180, 320), 3)  # density varies by goods type
            chargeable_weight = round(max(actual_weight, volume_m3 * CUBIC_FACTOR), 1)

            rate_row = get_active_rate(carrier_id, lane_id, service_level_id, chargeable_weight, ship_date)
            if rate_row is None:
                continue

            # --- BUY SIDE: what we actually pay the carrier today ---
            linehaul_buy = max(chargeable_weight * float(rate_row.rate_per_kg), float(rate_row.min_charge))
            levy_pct = fuel_levy_for(ship_date)
            linehaul_buy_with_levy = linehaul_buy * (1 + levy_pct / 100)

            applied_acc = maybe_accessorials(lane_type, cust.customer_id, month_idx, n_months, storyline)
            acc_buy_cost = accessorial_cost(applied_acc, linehaul_buy, chargeable_weight)
            buy_cost = round(linehaul_buy_with_levy + acc_buy_cost, 2)

            # --- SELL SIDE: the customer's FIXED rate card, set at some point
            # in the past and not automatically re-synced to today's buy cost.
            # Fuel levy is a live pass-through (industry-standard practice),
            # applied symmetrically -- so fuel alone should not erode margin.
            # Accessorials are passed through at cost + a flat 10% handling
            # fee (thinner than the base linehaul markup), which is what
            # makes an accessorial-heavy mix shift erode blended margin even
            # when the base linehaul rate card is technically "fine".
            rc = get_active_rate_card(cust.customer_id, lane_id, service_level_id, chargeable_weight, ship_date)
            if rc is None:
                continue
            linehaul_sell = max(chargeable_weight * float(rc.sell_rate_per_kg), float(rc.sell_min_charge))
            linehaul_sell_with_levy = linehaul_sell * (1 + levy_pct / 100)
            acc_sell_price = round(acc_buy_cost * 1.10, 2)
            sell_price = round(linehaul_sell_with_levy + acc_sell_price, 2)

            margin_pct = round(100 * (sell_price - buy_cost) / sell_price, 3) if sell_price > 0 else 0.0

            rows.append(dict(
                ship_date=ship_date.isoformat(), customer_id=cust.customer_id, lane_id=lane_id,
                service_level_id=service_level_id, carrier_id=carrier_id,
                actual_weight_kg=actual_weight, volume_m3=volume_m3,
                chargeable_weight_kg=chargeable_weight,
                accessorials_applied="{" + ",".join(applied_acc) + "}",  # postgres text[] literal
                buy_cost=buy_cost, sell_price=sell_price, margin_pct=margin_pct,
            ))

shipments = pd.DataFrame(rows)
shipments.to_csv(f"{OUT}/shipments.csv", index=False)

print(f"Generated {len(shipments)} shipments across {shipments.customer_id.nunique()} customers, "
      f"{shipments.ship_date.min()} to {shipments.ship_date.max()}")
print()
print("Monthly avg margin% by storyline customer (sanity check):")
shipments["month"] = pd.to_datetime(shipments.ship_date).dt.to_period("M")
for cid in ["CUST01", "CUST02", "CUST03"]:
    sub = shipments[shipments.customer_id == cid].groupby("month").margin_pct.mean().round(2)
    print(f"\n{cid}:")
    print(sub.to_string())
