"use client";

import { useState, Fragment } from "react";
import type { Customer, MonthlyAccountMarginSummary } from "@/lib/types";
import MarginFlag from "./MarginFlag";
import MarginTrendChart from "./MarginTrendChart";

interface Props {
  customers: Customer[];
  summary: MonthlyAccountMarginSummary[];
}

export default function AccountHealthTable({ customers, summary }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const custMap = Object.fromEntries(customers.map((c) => [c.customer_id, c]));

  const latestMonth = summary.reduce((max, r) => (r.month > max ? r.month : max), summary[0]?.month ?? "");
  const latestRows = summary
    .filter((r) => r.month === latestMonth)
    .sort((a, b) => b.margin_gap_pp - a.margin_gap_pp);

  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left">
            <Th>Account</Th>
            <Th>Segment</Th>
            <Th align="right">Realized</Th>
            <Th align="right">Target</Th>
            <Th align="right">Gap (pp)</Th>
            <Th>Status</Th>
            <Th align="right">Shipments</Th>
          </tr>
        </thead>
        <tbody>
          {latestRows.map((row) => {
            const cust = custMap[row.customer_id];
            const isOpen = expanded === row.customer_id;
            const history = summary.filter((r) => r.customer_id === row.customer_id);
            return (
              <Fragment key={row.customer_id}>
                <tr
                  onClick={() => setExpanded(isOpen ? null : row.customer_id)}
                  className="border-b border-line last:border-0 cursor-pointer hover:bg-paper transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium">{cust?.customer_name ?? row.customer_id}</div>
                    <div className="waybill-code">{row.customer_id}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{cust?.segment}</td>
                  <td className="px-4 py-3 text-right font-mono">{row.realized_margin_pct.toFixed(1)}%</td>
                  <td className="px-4 py-3 text-right font-mono text-slate-400">
                    {row.target_margin_pct.toFixed(1)}%
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono font-medium ${
                      row.margin_gap_pp > 0 ? "text-rust" : "text-pine"
                    }`}
                  >
                    {row.margin_gap_pp > 0 ? "+" : ""}
                    {row.margin_gap_pp.toFixed(1)}
                  </td>
                  <td className="px-4 py-3">
                    <MarginFlag flag={row.margin_flag} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-400">
                    {row.shipment_count}
                    {row.low_confidence && <span title="Fewer than 8 shipments this month — read with caution">*</span>}
                  </td>
                </tr>
                {isOpen && (
                  <tr className="bg-paper border-b border-line">
                    <td colSpan={7} className="px-6 py-5">
                      <div className="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-6">
                        <div>
                          <div className="eyebrow mb-2">12-month margin trend vs. target</div>
                          <MarginTrendChart rows={history} />
                        </div>
                        <div className="space-y-3">
                          <div>
                            <div className="eyebrow">Accessorial-heavy share</div>
                            <div className="text-2xl font-display font-bold mt-1">
                              {row.accessorial_shipment_share_pct.toFixed(0)}%
                            </div>
                            <p className="text-xs text-slate-400 mt-1">
                              of shipments this month carried an accessorial charge. A rising share
                              alongside falling margin points to mix-shift erosion &mdash; accessorials
                              are passed through at a thinner markup than base linehaul.
                            </p>
                          </div>
                          <div className="pt-2 border-t border-line">
                            <div className="eyebrow">Reading this account</div>
                            <p className="text-xs text-slate-400 mt-1">
                              {readingNote(row, history)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function readingNote(row: MonthlyAccountMarginSummary, history: MonthlyAccountMarginSummary[]): string {
  const sorted = [...history].sort((a, b) => a.month.localeCompare(b.month));
  const breachMonths = sorted.filter((r) => r.margin_flag === "breach").length;
  const recentlyRecovered =
    sorted.length >= 3 &&
    sorted[sorted.length - 1].margin_flag === "ok" &&
    sorted.slice(-4, -1).some((r) => r.margin_flag !== "ok");

  if (row.margin_flag === "breach") {
    return "Margin is materially below target this month. Worth checking whether a carrier rate change or a shift toward higher-cost lanes/accessorials has moved faster than the rate card.";
  }
  if (recentlyRecovered) {
    return "This account was recently below target and has since recovered — consistent with a rate card correction taking effect.";
  }
  if (breachMonths > 0) {
    return `This account has breached target margin in ${breachMonths} of the last ${sorted.length} months — worth a rate card review even though the current month reads OK.`;
  }
  if (row.margin_flag === "warning") {
    return "Margin is trending below target without yet being a breach — a candidate for proactive review before it compounds.";
  }
  return "Margin has tracked close to target over the visible history — no action indicated.";
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th className={`px-4 py-3 eyebrow font-normal ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}
