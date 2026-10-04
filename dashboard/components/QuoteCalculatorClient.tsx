"use client";

import { useMemo, useState } from "react";
import { computeQuote, QuoteResult } from "@/lib/pricingEngine";
import type {
  Lane,
  Carrier,
  ServiceLevel,
  CarrierRate,
  FuelLevyMonth,
  Accessorial,
  Customer,
  CustomerRateCard,
} from "@/lib/types";
import RouteManifestCard from "./RouteManifestCard";
import MarginFlag from "./MarginFlag";

interface Props {
  lanes: Lane[];
  carriers: Carrier[];
  serviceLevels: ServiceLevel[];
  carrierRates: CarrierRate[];
  fuelLevyIndex: FuelLevyMonth[];
  accessorials: Accessorial[];
  customers: Customer[];
  customerRateCards: CustomerRateCard[];
}

const today = () => new Date().toISOString().slice(0, 10);

export default function QuoteCalculatorClient({
  lanes,
  carriers,
  serviceLevels,
  carrierRates,
  fuelLevyIndex,
  accessorials,
  customers,
  customerRateCards,
}: Props) {
  const [laneId, setLaneId] = useState(lanes[0]?.lane_id ?? "");
  const [serviceLevelId, setServiceLevelId] = useState(serviceLevels[1]?.service_level_id ?? "");
  const [customerId, setCustomerId] = useState<string>("");
  const [actualWeightKg, setActualWeightKg] = useState(180);
  const [volumeM3, setVolumeM3] = useState(0.7);
  const [quoteDate, setQuoteDate] = useState(today());
  const [selectedAccessorials, setSelectedAccessorials] = useState<string[]>([]);
  const [fuelStressPct, setFuelStressPct] = useState(0);

  const lane = lanes.find((l) => l.lane_id === laneId);

  const stressedFuelLevyIndex = useMemo(
    () => fuelLevyIndex.map((f) => ({ ...f, levy_pct: f.levy_pct * (1 + fuelStressPct / 100) })),
    [fuelLevyIndex, fuelStressPct]
  );

  const quote: QuoteResult | null = useMemo(() => {
    if (!laneId || !serviceLevelId || actualWeightKg <= 0 || volumeM3 <= 0) return null;
    try {
      return computeQuote({
        carrierRates,
        fuelLevyIndex: stressedFuelLevyIndex,
        accessorials,
        customerRateCards,
        laneId,
        serviceLevelId,
        actualWeightKg,
        volumeM3,
        customerId: customerId || null,
        quoteDate,
        appliedAccessorialIds: selectedAccessorials,
      });
    } catch {
      return null;
    }
  }, [
    laneId,
    serviceLevelId,
    actualWeightKg,
    volumeM3,
    customerId,
    quoteDate,
    selectedAccessorials,
    carrierRates,
    stressedFuelLevyIndex,
    accessorials,
    customerRateCards,
  ]);

  const carrier = quote ? carriers.find((c) => c.carrier_id === quote.carrierId) : undefined;
  const serviceLevel = serviceLevels.find((s) => s.service_level_id === serviceLevelId);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6 lg:gap-8 mt-6">
      {/* form */}
      <div className="card p-4 sm:p-6 h-fit space-y-5">
        <div>
          <label className="eyebrow block mb-1.5">Lane</label>
          <select
            className="w-full border border-line rounded-sm px-3 py-2.5 sm:py-2 text-base sm:text-sm bg-paper-card"
            value={laneId}
            onChange={(e) => setLaneId(e.target.value)}
          >
            {lanes.map((l) => (
              <option key={l.lane_id} value={l.lane_id}>
                {l.lane_id} &middot; {l.origin_city} &rarr; {l.dest_city} ({l.lane_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="eyebrow block mb-1.5">Service level</label>
          <select
            className="w-full border border-line rounded-sm px-3 py-2.5 sm:py-2 text-base sm:text-sm bg-paper-card"
            value={serviceLevelId}
            onChange={(e) => setServiceLevelId(e.target.value)}
          >
            {serviceLevels.map((s) => (
              <option key={s.service_level_id} value={s.service_level_id}>
                {s.service_name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="eyebrow block mb-1.5">Actual weight (kg)</label>
            <input
              type="number"
              min={0.1}
              step={0.1}
              className="w-full border border-line rounded-sm px-3 py-2.5 sm:py-2 text-base sm:text-sm font-mono bg-paper-card"
              value={actualWeightKg}
              onChange={(e) => setActualWeightKg(parseFloat(e.target.value) || 0)}
            />
          </div>
          <div>
            <label className="eyebrow block mb-1.5">Volume (m&sup3;)</label>
            <input
              type="number"
              min={0.01}
              step={0.01}
              className="w-full border border-line rounded-sm px-3 py-2.5 sm:py-2 text-base sm:text-sm font-mono bg-paper-card"
              value={volumeM3}
              onChange={(e) => setVolumeM3(parseFloat(e.target.value) || 0)}
            />
          </div>
        </div>

        <div>
          <label className="eyebrow block mb-1.5">Customer</label>
          <select
            className="w-full border border-line rounded-sm px-3 py-2.5 sm:py-2 text-base sm:text-sm bg-paper-card"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          >
            <option value="">New prospect (no rate card yet)</option>
            {customers.map((c) => (
              <option key={c.customer_id} value={c.customer_id}>
                {c.customer_name} ({c.segment})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="eyebrow block mb-1.5">Accessorials</label>
          <div className="space-y-1.5">
            {accessorials.map((a) => (
              <label key={a.accessorial_id} className="flex items-center gap-3 text-sm py-1.5 sm:py-0">
                <input
                  type="checkbox"
                  checked={selectedAccessorials.includes(a.accessorial_id)}
                  onChange={(e) => {
                    setSelectedAccessorials((prev) =>
                      e.target.checked
                        ? [...prev, a.accessorial_id]
                        : prev.filter((id) => id !== a.accessorial_id)
                    );
                  }}
                />
                {a.accessorial_name}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="eyebrow block mb-1.5">Quote date</label>
          <input
            type="date"
            className="w-full border border-line rounded-sm px-3 py-2.5 sm:py-2 text-base sm:text-sm font-mono bg-paper-card"
            value={quoteDate}
            onChange={(e) => setQuoteDate(e.target.value)}
          />
        </div>

        <div className="border-t border-line pt-4">
          <label className="eyebrow block mb-1.5">
            Scenario: stress-test fuel levy ({fuelStressPct > 0 ? "+" : ""}
            {fuelStressPct}%)
          </label>
          <input
            type="range"
            min={-20}
            max={40}
            step={5}
            value={fuelStressPct}
            onChange={(e) => setFuelStressPct(parseInt(e.target.value))}
            className="w-full accent-route"
          />
          <p className="text-xs text-slate-400 mt-1">
            Simulates a change in the carrier fuel levy index &mdash; useful for testing whether a
            quoted rate still holds margin if fuel moves before the contract is next reviewed.
          </p>
        </div>
      </div>

      {/* result */}
      <div>
        {quote && (
          <div className="lg:hidden fixed bottom-0 inset-x-0 z-10 bg-ink text-paper border-t border-ink-700 px-4 py-3 flex items-center justify-between shadow-[0_-2px_8px_rgba(0,0,0,0.15)]">
            <div className="flex items-center gap-3">
              <MarginFlag flag={quote.marginFlag} />
              <span className="font-mono text-xs text-paper/70">margin {quote.marginPct.toFixed(1)}%</span>
            </div>
            <span className="text-xl font-display font-bold">${quote.sellPrice.toFixed(2)}</span>
          </div>
        )}
        {quote && lane ? (
          <RouteManifestCard quote={quote} lane={lane} carrier={carrier} serviceLevel={serviceLevel} quoteDate={quoteDate} />
        ) : (
          <div className="card p-8 text-center text-slate-400 text-sm">
            No carrier services this lane/service/weight combination &mdash; try a different selection.
          </div>
        )}
      </div>
    </div>
  );
}
