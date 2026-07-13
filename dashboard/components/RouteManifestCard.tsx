import type { QuoteResult } from "@/lib/pricingEngine";
import type { Lane, Carrier, ServiceLevel } from "@/lib/types";
import MarginFlag from "./MarginFlag";
import MarginWaterfall from "./MarginWaterfall";

interface Props {
  quote: QuoteResult;
  lane: Lane;
  carrier: Carrier | undefined;
  serviceLevel: ServiceLevel | undefined;
  quoteDate: string;
}

export default function RouteManifestCard({ quote, lane, carrier, serviceLevel, quoteDate }: Props) {
  return (
    <div className="card overflow-hidden">
      {/* route header, styled like a waybill stub */}
      <div className="bg-ink text-paper px-6 py-5">
        <div className="flex items-center justify-between">
          <span className="waybill-code text-route-soft">
            {quote.laneId} &middot; {quoteDate}
          </span>
          <MarginFlag flag={quote.marginFlag} />
        </div>
        <div className="flex items-center gap-3 mt-3">
          <RoutePoint city={lane.origin_city} state={lane.origin_state} />
          <div className="flex-1 h-px bg-dotted-line opacity-60 relative top-[1px]" />
          <span className="text-xs font-mono text-paper/60">{lane.distance_km}km</span>
          <div className="flex-1 h-px bg-dotted-line opacity-60 relative top-[1px]" />
          <RoutePoint city={lane.dest_city} state={lane.dest_state} align="right" />
        </div>
      </div>

      {/* shipment particulars */}
      <div className="grid grid-cols-3 divide-x divide-line border-b border-line">
        <Particular label="Service" value={serviceLevel?.service_name ?? quote.serviceLevelId} />
        <Particular label="Chargeable weight" value={`${quote.chargeableWeightKg} kg`} />
        <Particular label="Carrier" value={carrier?.carrier_name ?? quote.carrierId} />
      </div>

      {/* margin waterfall */}
      <div className="px-6 py-5">
        <MarginWaterfall
          linehaulBuyWithLevy={quote.linehaulBuy * (1 + quote.fuelLevyPct / 100)}
          accessorialBuy={quote.accessorialBuy}
          buyCost={quote.buyCost}
          sellPrice={quote.sellPrice}
          marginPct={quote.marginPct}
          targetMarginPct={quote.targetMarginPct}
          flag={quote.marginFlag}
        />
      </div>

      <div className="px-6 py-3 bg-paper border-t border-line flex items-center justify-between">
        <span className="text-xs text-slate-400">
          Fuel levy this month: <span className="font-mono">{quote.fuelLevyPct.toFixed(1)}%</span>
          {!quote.usedRateCard && (
            <span className="ml-3">
              &middot; no existing rate card for this customer/lane &mdash; quoted at a default 25% markup
            </span>
          )}
        </span>
        <span className="text-2xl font-display font-bold">${quote.sellPrice.toFixed(2)}</span>
      </div>
    </div>
  );
}

function RoutePoint({ city, state, align = "left" }: { city: string; state: string; align?: "left" | "right" }) {
  return (
    <div className={align === "right" ? "text-right" : ""}>
      <div className="text-lg font-display font-bold leading-tight">{city}</div>
      <div className="text-xs text-paper/60 font-mono">{state}</div>
    </div>
  );
}

function Particular({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-6 py-3">
      <div className="eyebrow">{label}</div>
      <div className="text-sm font-medium mt-0.5">{value}</div>
    </div>
  );
}
