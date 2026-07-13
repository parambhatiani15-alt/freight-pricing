import sys
sys.path.insert(0, "/home/claude/freight-pricing/engine")
import pandas as pd
from datetime import date
from pricing_engine import compute_quote, monthly_account_margin_summary

OUT = "/home/claude/freight-pricing/data"

carriers = pd.read_csv(f"{OUT}/carriers.csv")
lanes = pd.read_csv(f"{OUT}/lanes.csv")
carrier_rates = pd.read_csv(f"{OUT}/carrier_rates.csv", parse_dates=["effective_from", "effective_to"])
fuel_levy_index = pd.read_csv(f"{OUT}/fuel_levy_index.csv", parse_dates=["month"])
accessorials = pd.read_csv(f"{OUT}/accessorials.csv")
customers = pd.read_csv(f"{OUT}/customers.csv")
customer_rate_cards = pd.read_csv(f"{OUT}/customer_rate_cards.csv", parse_dates=["effective_from", "effective_to"])
shipments = pd.read_csv(f"{OUT}/shipments.csv")


def parse_pg_array(s):
    if not isinstance(s, str) or s in ("{}", ""):
        return []
    return [x for x in s.strip("{}").split(",") if x]


shipments["accessorials_applied"] = shipments["accessorials_applied"].apply(parse_pg_array)
shipments["shipment_id"] = range(1, len(shipments) + 1)

# --- Sanity test the live quoting engine on a few illustrative scenarios ---
print("=" * 70)
print("QUOTE ENGINE SANITY CHECKS")
print("=" * 70)

test_cases = [
    dict(lane_id="L01", service_level_id="SVC_STD", actual_weight_kg=250, volume_m3=0.9,
         customer_id="CUST05", quote_date=date(2026, 6, 1), applied_accessorial_ids=[]),
    dict(lane_id="L04", service_level_id="SVC_STD", actual_weight_kg=800, volume_m3=3.0,
         customer_id="CUST03", quote_date=date(2026, 6, 1), applied_accessorial_ids=["ACC_TAILLIFT"]),
    dict(lane_id="L08", service_level_id="SVC_ECO", actual_weight_kg=120, volume_m3=0.5,
         customer_id=None, quote_date=date(2026, 6, 1), applied_accessorial_ids=["ACC_REMOTE"]),
]
for tc in test_cases:
    q = compute_quote(carrier_rates=carrier_rates, fuel_levy_index=fuel_levy_index,
                       accessorials_df=accessorials, customer_rate_cards=customer_rate_cards, **tc)
    print(f"\nLane {q.lane_id} / {q.service_level_id} / {q.chargeable_weight_kg}kg / carrier {q.carrier_id}")
    print(f"  buy_cost=${q.buy_cost}  sell_price=${q.sell_price}  "
          f"margin={q.margin_pct}% (target {q.target_margin_pct}%) -> {q.margin_flag}")

# --- Build the monthly account margin summary (the Portfolio Health table) ---
print("\n" + "=" * 70)
print("MONTHLY ACCOUNT MARGIN SUMMARY")
print("=" * 70)
summary = monthly_account_margin_summary(shipments, customer_rate_cards)
summary.to_csv(f"{OUT}/monthly_account_margin_summary.csv", index=False)
print(f"\n{len(summary)} rows written to monthly_account_margin_summary.csv")

print("\nMost recent month, all accounts, sorted by margin gap (worst first):")
latest_month = summary.month.max()
latest = summary[summary.month == latest_month].sort_values("margin_gap_pp", ascending=False)
cust_names = dict(zip(customers.customer_id, customers.customer_name))
latest = latest.assign(customer_name=latest.customer_id.map(cust_names))
cols = ["customer_id", "customer_name", "realized_margin_pct", "target_margin_pct", "margin_gap_pp", "margin_flag", "shipment_count"]
print(latest[cols].to_string(index=False))

print("\nFlag counts across full history:")
print(summary.margin_flag.value_counts().to_string())
