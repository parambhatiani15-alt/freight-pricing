import type { MonthlyAccountMarginSummary } from "@/lib/types";

export default function PortfolioSummaryCards({ latestRows }: { latestRows: MonthlyAccountMarginSummary[] }) {
  const totalAccounts = latestRows.length;
  const atRisk = latestRows.filter((r) => r.margin_flag !== "ok").length;
  const breaches = latestRows.filter((r) => r.margin_flag === "breach").length;

  const totalBuy = latestRows.reduce((s, r) => s + r.total_buy_cost, 0);
  const totalSell = latestRows.reduce((s, r) => s + r.total_sell_price, 0);
  const blendedMargin = totalSell > 0 ? (100 * (totalSell - totalBuy)) / totalSell : 0;

  const month = latestRows[0]?.month?.slice(0, 7) ?? "";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
      <Card label="Reporting month" value={month} mono />
      <Card label="Blended portfolio margin" value={`${blendedMargin.toFixed(1)}%`} />
      <Card
        label="Accounts at risk"
        value={`${atRisk} / ${totalAccounts}`}
        tone={atRisk > 0 ? "rust" : "pine"}
      />
      <Card label="In breach" value={`${breaches}`} tone={breaches > 0 ? "rust" : "pine"} />
    </div>
  );
}

function Card({
  label,
  value,
  tone,
  mono = false,
}: {
  label: string;
  value: string;
  tone?: "rust" | "pine";
  mono?: boolean;
}) {
  const toneClass = tone === "rust" ? "text-rust" : tone === "pine" ? "text-pine" : "text-ink";
  return (
    <div className="card p-4">
      <div className="eyebrow">{label}</div>
      <div className={`text-2xl font-display font-bold mt-1 ${toneClass} ${mono ? "font-mono text-lg" : ""}`}>
        {value}
      </div>
    </div>
  );
}
