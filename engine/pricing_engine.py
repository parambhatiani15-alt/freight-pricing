"""
Freight Pricing & Margin Monitoring Engine
===========================================

This is the reference calculation engine for the project: given a lane,
weight, service level and customer, it computes a quote (with a full
margin waterfall) the same way the synthetic shipment history was
generated, and it computes realized-margin monitoring against that
history with a root-cause breakdown.

It is deliberately dependency-light (pandas only) so it's easy to read,
test, and reuse from a batch script. The live "Quote Calculator" page in
the Next.js dashboard uses a TypeScript port of the compute_quote() logic
for interactivity; this module is the audited source of truth used to (a)
generate the historical dataset and (b) compute the pre-aggregated margin
monitoring table that gets pushed to Supabase. See README for the full
architecture note and why the logic is duplicated in two languages.

ASSUMPTIONS (stated explicitly — see README for the full honesty audit):
  - Chargeable weight = max(actual kg, volume_m3 * 250). 250 kg/m3 is an
    illustrative AU road-freight cubic conversion factor; real factors vary
    by carrier/mode (e.g. air freight commonly uses 333 kg/m3).
  - Fuel levy is modelled as a live, symmetric pass-through applied to both
    buy-side and sell-side linehaul. This matches common industry practice
    (fuel levies are usually a contracted % that moves with an index rather
    than being baked into the base rate) but real contracts vary — some
    lock a fuel levy for a period, which would reintroduce fuel-driven
    margin risk on top of what's modelled here.
  - Accessorials are passed through to the customer at cost + a flat 10%
    handling fee — thinner than the base linehaul markup. This is a
    simplification; real accessorial pricing policies vary by operator.
  - Carrier selection in the quoting engine picks the cheapest ELIGIBLE
    carrier for the lane/service/weight combination. This is a lightweight
    optimization, not a full multi-constraint carrier allocation model
    (that would be the RFP/tender-optimization project, out of scope here).
"""
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass, field
from datetime import date

CUBIC_FACTOR_KG_PER_M3 = 250
ACCESSORIAL_HANDLING_MARKUP = 0.10  # 10% on top of accessorial cost when passed to customer

MARGIN_WARNING_THRESHOLD_PP = 3.0   # percentage points below target -> "warning"
MARGIN_BREACH_THRESHOLD_PP = 6.0    # percentage points below target -> "breach"


@dataclass
class QuoteResult:
    lane_id: str
    service_level_id: str
    chargeable_weight_kg: float
    carrier_id: str
    linehaul_buy: float
    fuel_levy_pct: float
    accessorial_buy: float
    buy_cost: float
    linehaul_sell: float
    accessorial_sell: float
    sell_price: float
    margin_pct: float
    target_margin_pct: float
    margin_flag: str  # 'ok' | 'warning' | 'breach'
    accessorials_applied: list = field(default_factory=list)


def chargeable_weight(actual_weight_kg: float, volume_m3: float) -> float:
    """Greater of actual weight and volumetric ('cubic') weight."""
    return max(actual_weight_kg, volume_m3 * CUBIC_FACTOR_KG_PER_M3)


def _active(df: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    return df[(df.effective_from <= as_of) & ((df.effective_to.isna()) | (df.effective_to >= as_of))]


def cheapest_eligible_carrier_rate(carrier_rates: pd.DataFrame, lane_id: str, service_level_id: str,
                                    weight_kg: float, as_of: date) -> pd.Series | None:
    """
    Lightweight carrier-selection optimization: among carriers servicing this
    lane/service/weight-break combination and active as of `as_of`, return
    the cheapest rate row. (Not a constrained multi-lane allocation —
    see module docstring.)
    """
    as_of_ts = pd.Timestamp(as_of)
    pool = carrier_rates[
        (carrier_rates.lane_id == lane_id) &
        (carrier_rates.service_level_id == service_level_id) &
        (carrier_rates.weight_break_min_kg <= weight_kg) &
        ((carrier_rates.weight_break_max_kg.isna()) | (carrier_rates.weight_break_max_kg > weight_kg))
    ]
    pool = _active(pool, as_of_ts)
    if pool.empty:
        return None
    pool = pool.assign(_implied_cost=pool.rate_per_kg * weight_kg)
    pool = pool.assign(_implied_cost=pool[["_implied_cost", "min_charge"]].max(axis=1))
    return pool.sort_values("_implied_cost").iloc[0]


def compute_accessorial_cost(accessorials_df: pd.DataFrame, applied_ids: list[str],
                              linehaul_cost: float, weight_kg: float) -> float:
    total = 0.0
    for acc_id in applied_ids:
        row = accessorials_df[accessorials_df.accessorial_id == acc_id]
        if row.empty:
            continue
        row = row.iloc[0]
        if row.charge_type == "flat":
            total += float(row.amount)
        elif row.charge_type == "per_kg":
            total += float(row.amount) * weight_kg
        elif row.charge_type == "pct_of_linehaul":
            total += linehaul_cost * (float(row.amount) / 100)
    return round(total, 2)


def margin_flag(margin_pct: float, target_margin_pct: float) -> str:
    gap = target_margin_pct - margin_pct
    if gap >= MARGIN_BREACH_THRESHOLD_PP:
        return "breach"
    if gap >= MARGIN_WARNING_THRESHOLD_PP:
        return "warning"
    return "ok"


def compute_quote(
    *,
    carrier_rates: pd.DataFrame,
    fuel_levy_index: pd.DataFrame,
    accessorials_df: pd.DataFrame,
    customer_rate_cards: pd.DataFrame,
    lane_id: str,
    service_level_id: str,
    actual_weight_kg: float,
    volume_m3: float,
    customer_id: str | None,
    quote_date: date,
    applied_accessorial_ids: list[str] | None = None,
    default_markup_pct_if_prospect: float = 0.25,
) -> QuoteResult:
    """
    Compute a full quote with margin waterfall for a given lane/weight/
    service/customer. If customer_id is None (a prospect / ad-hoc quote),
    a default markup is applied directly over the live buy cost instead of
    looking up a fixed rate card.
    """
    applied_accessorial_ids = applied_accessorial_ids or []
    w = chargeable_weight(actual_weight_kg, volume_m3)

    rate_row = cheapest_eligible_carrier_rate(carrier_rates, lane_id, service_level_id, w, quote_date)
    if rate_row is None:
        raise ValueError(f"No carrier services lane {lane_id} / {service_level_id} at this weight.")

    linehaul_buy = max(w * float(rate_row.rate_per_kg), float(rate_row.min_charge))

    month_start = pd.Timestamp(quote_date.replace(day=1))
    levy_row = fuel_levy_index[fuel_levy_index.month == month_start]
    fuel_levy_pct = float(levy_row.levy_pct.iloc[0]) if not levy_row.empty else float(fuel_levy_index.levy_pct.iloc[-1])

    accessorial_buy = compute_accessorial_cost(accessorials_df, applied_accessorial_ids, linehaul_buy, w)
    buy_cost = round(linehaul_buy * (1 + fuel_levy_pct / 100) + accessorial_buy, 2)

    rc = None
    if customer_id is not None:
        pool = customer_rate_cards[
            (customer_rate_cards.customer_id == customer_id) &
            (customer_rate_cards.lane_id == lane_id) &
            (customer_rate_cards.service_level_id == service_level_id) &
            (customer_rate_cards.weight_break_min_kg <= w) &
            ((customer_rate_cards.weight_break_max_kg.isna()) | (customer_rate_cards.weight_break_max_kg > w))
        ]
        pool = _active(pool, pd.Timestamp(quote_date))
        rc = pool.iloc[0] if not pool.empty else None

    if rc is not None:
        linehaul_sell = max(w * float(rc.sell_rate_per_kg), float(rc.sell_min_charge))
        target_margin_pct = float(rc.target_margin_pct)
    else:
        # prospect / no existing rate card: quote fresh off today's buy cost
        markup = default_markup_pct_if_prospect
        linehaul_sell = linehaul_buy * (1 + markup)
        target_margin_pct = round(100 * markup / (1 + markup), 3)

    linehaul_sell_with_levy = linehaul_sell * (1 + fuel_levy_pct / 100)
    accessorial_sell = round(accessorial_buy * (1 + ACCESSORIAL_HANDLING_MARKUP), 2)
    sell_price = round(linehaul_sell_with_levy + accessorial_sell, 2)

    margin_pct = round(100 * (sell_price - buy_cost) / sell_price, 3) if sell_price > 0 else 0.0
    flag = margin_flag(margin_pct, target_margin_pct)

    return QuoteResult(
        lane_id=lane_id, service_level_id=service_level_id, chargeable_weight_kg=round(w, 1),
        carrier_id=str(rate_row.carrier_id), linehaul_buy=round(linehaul_buy, 2), fuel_levy_pct=fuel_levy_pct,
        accessorial_buy=accessorial_buy, buy_cost=buy_cost, linehaul_sell=round(linehaul_sell, 2),
        accessorial_sell=accessorial_sell, sell_price=sell_price, margin_pct=margin_pct,
        target_margin_pct=target_margin_pct, margin_flag=flag, accessorials_applied=applied_accessorial_ids,
    )


# ---------------------------------------------------------------------------
# Margin monitoring: realized margin vs. target, with a root-cause split
# ---------------------------------------------------------------------------

def attach_applicable_target_margin(shipments: pd.DataFrame, customer_rate_cards: pd.DataFrame) -> pd.DataFrame:
    """
    Matches each shipment to the specific rate card row that actually priced
    it (same customer/lane/service level/weight break, active on ship_date)
    and attaches that row's target_margin_pct. This is deliberately done at
    shipment grain rather than averaging a customer's whole rate-card book,
    so the target reflects the lanes the customer actually ships on (a
    high-volume lane's rate correction should be visible in the blended
    target even if 11 other, rarely-used lanes weren't touched).
    """
    s = shipments.copy()
    s["ship_date"] = pd.to_datetime(s["ship_date"])
    rc = customer_rate_cards.copy()
    rc["effective_from"] = pd.to_datetime(rc["effective_from"])
    rc["effective_to"] = pd.to_datetime(rc["effective_to"])

    merged = s.merge(
        rc[["customer_id", "lane_id", "service_level_id", "weight_break_min_kg", "weight_break_max_kg",
            "target_margin_pct", "effective_from", "effective_to"]],
        on=["customer_id", "lane_id", "service_level_id"], how="left", suffixes=("", "_rc"),
    )
    mask = (
        (merged.chargeable_weight_kg >= merged.weight_break_min_kg) &
        ((merged.weight_break_max_kg.isna()) | (merged.chargeable_weight_kg < merged.weight_break_max_kg)) &
        (merged.effective_from <= merged.ship_date) &
        ((merged.effective_to.isna()) | (merged.effective_to >= merged.ship_date))
    )
    merged = merged[mask]
    # one match expected per shipment; keep first if duplicates slip through.
    # Use shipment_id if present, else the original row index (accessorials
    # is a list column so it can't be used directly in drop_duplicates).
    if "shipment_id" in merged.columns:
        merged = merged.drop_duplicates(subset=["shipment_id"], keep="first")
    else:
        merged = merged[~merged.index.duplicated(keep="first")]
    return merged


def monthly_account_margin_summary(shipments: pd.DataFrame, customer_rate_cards: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates shipment-level realized margin to customer x month, compares
    against the target margin that was actually applicable to the shipments
    that moved in that month (see attach_applicable_target_margin), and
    flags accounts falling meaningfully short.

    Root-cause hint columns are heuristic, not a full attribution model:
      - accessorial_shipment_share_pct: % of shipments in the month that
        carried at least one accessorial. A rising share alongside falling
        margin is consistent with mix-shift-driven erosion.
      - low_confidence: months with under 8 shipments are noisier and
        should be read with more caution.
    """
    s = attach_applicable_target_margin(shipments, customer_rate_cards)
    s["month"] = s["ship_date"].dt.to_period("M").dt.to_timestamp()
    s["has_accessorial"] = s["accessorials_applied"].apply(lambda x: isinstance(x, list) and len(x) > 0)

    grp = s.groupby(["customer_id", "month"]).agg(
        shipment_count=("buy_cost", "count"),
        total_buy_cost=("buy_cost", "sum"),
        total_sell_price=("sell_price", "sum"),
        accessorial_shipment_count=("has_accessorial", "sum"),
        target_margin_pct=("target_margin_pct", "mean"),  # mean of applicable per-shipment targets = volume-weighted
    ).reset_index()

    grp["realized_margin_pct"] = round(100 * (grp.total_sell_price - grp.total_buy_cost) / grp.total_sell_price, 3)
    grp["target_margin_pct"] = grp["target_margin_pct"].round(3)
    grp["accessorial_shipment_share_pct"] = round(100 * grp.accessorial_shipment_count / grp.shipment_count, 2)
    grp["margin_gap_pp"] = round(grp.target_margin_pct - grp.realized_margin_pct, 3)
    grp["margin_flag"] = grp.apply(lambda r: margin_flag(r.realized_margin_pct, r.target_margin_pct), axis=1)
    grp["low_confidence"] = grp.shipment_count < 8

    return grp.sort_values(["customer_id", "month"])
