/**
 * Freight Pricing Engine (TypeScript port)
 * ==========================================
 * Mirrors engine/pricing_engine.py's compute_quote() logic exactly, so the
 * live Quote Calculator can respond instantly in the browser without a
 * round trip to a Python service. The Python module is the audited source
 * of truth (it's what generated and validated the historical dataset);
 * this port is unit-tested against a handful of the same scenarios to keep
 * the two in sync -- see /engine/pricing_engine.py's module docstring for
 * the full architecture note and the assumptions this logic makes
 * (cubic weight factor, fuel levy pass-through model, accessorial markup).
 */
import type { CarrierRate, FuelLevyMonth, Accessorial, CustomerRateCard } from "./types";

export const CUBIC_FACTOR_KG_PER_M3 = 250;
export const ACCESSORIAL_HANDLING_MARKUP = 0.1;
export const MARGIN_WARNING_THRESHOLD_PP = 3.0;
export const MARGIN_BREACH_THRESHOLD_PP = 6.0;

export interface QuoteResult {
  laneId: string;
  serviceLevelId: string;
  chargeableWeightKg: number;
  carrierId: string;
  linehaulBuy: number;
  fuelLevyPct: number;
  accessorialBuy: number;
  buyCost: number;
  linehaulSell: number;
  accessorialSell: number;
  sellPrice: number;
  marginPct: number;
  targetMarginPct: number;
  marginFlag: "ok" | "warning" | "breach";
  usedRateCard: boolean;
}

export function chargeableWeight(actualWeightKg: number, volumeM3: number): number {
  return Math.max(actualWeightKg, volumeM3 * CUBIC_FACTOR_KG_PER_M3);
}

function isActive(effFrom: string, effTo: string | null, asOf: string): boolean {
  return effFrom <= asOf && (effTo === null || effTo >= asOf);
}

/** Cheapest eligible carrier for a lane/service/weight combo, active as of the quote date. */
export function cheapestEligibleCarrierRate(
  carrierRates: CarrierRate[],
  laneId: string,
  serviceLevelId: string,
  weightKg: number,
  asOf: string
): CarrierRate | null {
  const pool = carrierRates.filter(
    (r) =>
      r.lane_id === laneId &&
      r.service_level_id === serviceLevelId &&
      r.weight_break_min_kg <= weightKg &&
      (r.weight_break_max_kg === null || r.weight_break_max_kg > weightKg) &&
      isActive(r.effective_from, r.effective_to, asOf)
  );
  if (pool.length === 0) return null;
  let best = pool[0];
  let bestCost = Math.max(best.rate_per_kg * weightKg, best.min_charge);
  for (const r of pool.slice(1)) {
    const cost = Math.max(r.rate_per_kg * weightKg, r.min_charge);
    if (cost < bestCost) {
      best = r;
      bestCost = cost;
    }
  }
  return best;
}

export function computeAccessorialCost(
  accessorials: Accessorial[],
  appliedIds: string[],
  linehaulCost: number,
  weightKg: number
): number {
  let total = 0;
  for (const id of appliedIds) {
    const row = accessorials.find((a) => a.accessorial_id === id);
    if (!row) continue;
    if (row.charge_type === "flat") total += row.amount;
    else if (row.charge_type === "per_kg") total += row.amount * weightKg;
    else if (row.charge_type === "pct_of_linehaul") total += linehaulCost * (row.amount / 100);
  }
  return Math.round(total * 100) / 100;
}

export function marginFlag(marginPct: number, targetMarginPct: number): "ok" | "warning" | "breach" {
  const gap = targetMarginPct - marginPct;
  if (gap >= MARGIN_BREACH_THRESHOLD_PP) return "breach";
  if (gap >= MARGIN_WARNING_THRESHOLD_PP) return "warning";
  return "ok";
}

export interface ComputeQuoteInput {
  carrierRates: CarrierRate[];
  fuelLevyIndex: FuelLevyMonth[];
  accessorials: Accessorial[];
  customerRateCards: CustomerRateCard[];
  laneId: string;
  serviceLevelId: string;
  actualWeightKg: number;
  volumeM3: number;
  customerId: string | null;
  quoteDate: string; // 'YYYY-MM-DD'
  appliedAccessorialIds?: string[];
  defaultMarkupIfProspect?: number;
}

export function computeQuote(input: ComputeQuoteInput): QuoteResult {
  const {
    carrierRates,
    fuelLevyIndex,
    accessorials,
    customerRateCards,
    laneId,
    serviceLevelId,
    actualWeightKg,
    volumeM3,
    customerId,
    quoteDate,
    appliedAccessorialIds = [],
    defaultMarkupIfProspect = 0.25,
  } = input;

  const w = chargeableWeight(actualWeightKg, volumeM3);
  const rateRow = cheapestEligibleCarrierRate(carrierRates, laneId, serviceLevelId, w, quoteDate);
  if (!rateRow) {
    throw new Error(`No carrier services lane ${laneId} / ${serviceLevelId} at ${w}kg.`);
  }

  const linehaulBuy = Math.max(w * rateRow.rate_per_kg, rateRow.min_charge);
  const monthStart = quoteDate.slice(0, 7) + "-01";
  const levyRow = fuelLevyIndex.find((f) => f.month === monthStart);
  const fuelLevyPct = levyRow ? levyRow.levy_pct : fuelLevyIndex[fuelLevyIndex.length - 1]?.levy_pct ?? 20;

  const accessorialBuy = computeAccessorialCost(accessorials, appliedAccessorialIds, linehaulBuy, w);
  const buyCost = round2(linehaulBuy * (1 + fuelLevyPct / 100) + accessorialBuy);

  let linehaulSell: number;
  let targetMarginPct: number;
  let usedRateCard = false;

  const rc = customerId
    ? customerRateCards.find(
        (c) =>
          c.customer_id === customerId &&
          c.lane_id === laneId &&
          c.service_level_id === serviceLevelId &&
          c.weight_break_min_kg <= w &&
          (c.weight_break_max_kg === null || c.weight_break_max_kg > w) &&
          isActive(c.effective_from, c.effective_to, quoteDate)
      )
    : undefined;

  if (rc) {
    linehaulSell = Math.max(w * rc.sell_rate_per_kg, rc.sell_min_charge);
    targetMarginPct = rc.target_margin_pct;
    usedRateCard = true;
  } else {
    const markup = defaultMarkupIfProspect;
    linehaulSell = linehaulBuy * (1 + markup);
    targetMarginPct = round3((100 * markup) / (1 + markup));
  }

  const linehaulSellWithLevy = linehaulSell * (1 + fuelLevyPct / 100);
  const accessorialSell = round2(accessorialBuy * (1 + ACCESSORIAL_HANDLING_MARKUP));
  const sellPrice = round2(linehaulSellWithLevy + accessorialSell);
  const marginPct = sellPrice > 0 ? round3((100 * (sellPrice - buyCost)) / sellPrice) : 0;

  return {
    laneId,
    serviceLevelId,
    chargeableWeightKg: round1(w),
    carrierId: rateRow.carrier_id,
    linehaulBuy: round2(linehaulBuy),
    fuelLevyPct,
    accessorialBuy,
    buyCost,
    linehaulSell: round2(linehaulSell),
    accessorialSell,
    sellPrice,
    marginPct,
    targetMarginPct,
    marginFlag: marginFlag(marginPct, targetMarginPct),
    usedRateCard,
  };
}

function round1(n: number) {
  return Math.round(n * 10) / 10;
}
function round2(n: number) {
  return Math.round(n * 100) / 100;
}
function round3(n: number) {
  return Math.round(n * 1000) / 1000;
}
