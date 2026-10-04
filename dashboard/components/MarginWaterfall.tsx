import type { MarginFlag as MarginFlagType } from "@/lib/types";

interface Props {
  linehaulBuyWithLevy: number;
  accessorialBuy: number;
  buyCost: number;
  sellPrice: number;
  marginPct: number;
  targetMarginPct: number;
  flag: MarginFlagType;
}

const FLAG_COLOR: Record<MarginFlagType, string> = {
  ok: "bg-pine",
  warning: "bg-amber",
  breach: "bg-rust",
};

export default function MarginWaterfall({
  linehaulBuyWithLevy,
  accessorialBuy,
  buyCost,
  sellPrice,
  marginPct,
  targetMarginPct,
  flag,
}: Props) {
  const total = Math.max(sellPrice, buyCost, 1);
  const linehaulPct = (linehaulBuyWithLevy / total) * 100;
  const accessorialPct = (accessorialBuy / total) * 100;
  const marginSegmentPct = Math.max(((sellPrice - buyCost) / total) * 100, 0);
  const targetBuyCost = sellPrice * (1 - targetMarginPct / 100);
  const targetMarkerPct = Math.min((targetBuyCost / total) * 100, 100);

  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 mb-2">
        <span className="eyebrow">Margin waterfall</span>
        <span className="font-mono text-xs text-slate-400">
          target {targetMarginPct.toFixed(1)}% &middot; actual{" "}
          <span
            className={
              flag === "ok" ? "text-pine font-medium" : flag === "warning" ? "text-amber font-medium" : "text-rust font-medium"
            }
          >
            {marginPct.toFixed(1)}%
          </span>
        </span>
      </div>

      <div className="relative h-9 w-full rounded-sm overflow-hidden border border-line bg-paper">
        <div className="h-full flex" style={{ width: "100%" }}>
          <div
            className="h-full bg-ink-700"
            style={{ width: `${linehaulPct}%` }}
            title={`Linehaul (incl. fuel levy): $${linehaulBuyWithLevy.toFixed(2)}`}
          />
          <div
            className="h-full bg-slate-400"
            style={{ width: `${accessorialPct}%` }}
            title={`Accessorials: $${accessorialBuy.toFixed(2)}`}
          />
          <div
            className={`h-full ${FLAG_COLOR[flag]}`}
            style={{ width: `${marginSegmentPct}%` }}
            title={`Margin: ${marginPct.toFixed(1)}%`}
          />
        </div>
        {/* target margin marker */}
        <div
          className="absolute top-0 bottom-0 w-0 border-l-2 border-dashed border-ink/60"
          style={{ left: `${targetMarkerPct}%` }}
          title={`Target margin boundary (${targetMarginPct.toFixed(1)}%)`}
        />
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-slate-400 font-mono">
        <LegendDot className="bg-ink-700" label="linehaul" />
        <LegendDot className="bg-slate-400" label="accessorials" />
        <LegendDot className={FLAG_COLOR[flag]} label="margin" />
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 border-t-2 border-dashed border-ink/60" /> target line
        </span>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 sm:gap-x-6 gap-y-1.5 mt-4 font-mono text-sm">
        <Row label="Linehaul + fuel levy" value={linehaulBuyWithLevy} />
        <Row label="Accessorials" value={accessorialBuy} />
        <Row label="Buy cost (total)" value={buyCost} strong />
        <Row label="Sell price (total)" value={sellPrice} strong />
      </dl>
    </div>
  );
}

function LegendDot({ className, label }: { className: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-sm ${className}`} /> {label}
    </span>
  );
}

function Row({ label, value, strong = false }: { label: string; value: number; strong?: boolean }) {
  return (
    <>
      <dt className={`text-slate-400 ${strong ? "font-medium text-ink" : ""}`}>{label}</dt>
      <dd className={`text-right ${strong ? "font-semibold text-ink" : "text-ink"}`}>
        ${value.toFixed(2)}
      </dd>
    </>
  );
}
