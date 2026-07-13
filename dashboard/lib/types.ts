export interface Carrier {
  carrier_id: string;
  carrier_name: string;
  mode: "road" | "intermodal";
  on_time_pct: number;
  tender_accept_pct: number;
  damage_rate_pct: number;
  notes: string | null;
}

export interface Lane {
  lane_id: string;
  origin_city: string;
  origin_state: string;
  dest_city: string;
  dest_state: string;
  distance_km: number;
  lane_type: "metro" | "interstate" | "regional";
}

export interface ServiceLevel {
  service_level_id: string;
  service_name: string;
  target_transit_days: number;
}

export interface CarrierRate {
  rate_id: number;
  carrier_id: string;
  lane_id: string;
  service_level_id: string;
  weight_break_min_kg: number;
  weight_break_max_kg: number | null;
  rate_per_kg: number;
  min_charge: number;
  effective_from: string;
  effective_to: string | null;
}

export interface FuelLevyMonth {
  month: string;
  levy_pct: number;
}

export interface Accessorial {
  accessorial_id: string;
  accessorial_name: string;
  charge_type: "flat" | "per_kg" | "pct_of_linehaul";
  amount: number;
}

export interface Customer {
  customer_id: string;
  customer_name: string;
  segment: "SME" | "Mid-Market" | "Enterprise";
  volume_tier: "Low" | "Medium" | "High";
  onboarded_date: string;
}

export interface CustomerRateCard {
  rate_card_id: number;
  customer_id: string;
  lane_id: string;
  service_level_id: string;
  weight_break_min_kg: number;
  weight_break_max_kg: number | null;
  sell_rate_per_kg: number;
  sell_min_charge: number;
  markup_pct: number;
  target_margin_pct: number;
  effective_from: string;
  effective_to: string | null;
}

export interface MonthlyAccountMarginSummary {
  customer_id: string;
  month: string;
  shipment_count: number;
  total_buy_cost: number;
  total_sell_price: number;
  accessorial_shipment_count: number;
  target_margin_pct: number;
  realized_margin_pct: number;
  accessorial_shipment_share_pct: number;
  margin_gap_pp: number;
  margin_flag: "ok" | "warning" | "breach";
  low_confidence: boolean;
}

export type MarginFlag = "ok" | "warning" | "breach";
