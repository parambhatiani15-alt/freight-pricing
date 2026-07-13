import { getSupabase } from "@/lib/supabase";
import type { Customer, MonthlyAccountMarginSummary } from "@/lib/types";
import PortfolioSummaryCards from "@/components/PortfolioSummaryCards";
import AccountHealthTable from "@/components/AccountHealthTable";

export const revalidate = 0;

export default async function PortfolioHealthPage() {
  const supabase = getSupabase();
  if (!supabase) {
    return (
      <div className="mt-10 card p-6 border-rust/40">
        <h2 className="font-display font-bold text-lg text-rust">Supabase is not configured</h2>
        <p className="text-sm text-slate-400 mt-3">
          Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local
          (see .env.local.example), then restart the dev server.
        </p>
      </div>
    );
  }

  const [customersR, summaryR] = await Promise.all([
    supabase.from("customers").select("*"),
    supabase.from("monthly_account_margin_summary").select("*").order("month"),
  ]);

  if (customersR.error || summaryR.error) {
    const err = customersR.error ?? summaryR.error;
    return (
      <div className="mt-10 card p-6 border-rust/40">
        <h2 className="font-display font-bold text-lg text-rust">Couldn&apos;t load margin data</h2>
        <p className="text-sm text-slate-400 mt-2 font-mono">{err?.message}</p>
        <p className="text-sm text-slate-400 mt-3">
          Check that the schema and seed SQL have been applied in Supabase, and that
          NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY are set correctly.
        </p>
      </div>
    );
  }

  const customers = (customersR.data as Customer[]) ?? [];
  const summary = (summaryR.data as MonthlyAccountMarginSummary[]) ?? [];
  const latestMonth = summary.reduce((max, r) => (r.month > max ? r.month : max), summary[0]?.month ?? "");
  const latestRows = summary.filter((r) => r.month === latestMonth);

  return (
    <div className="mt-10">
      <div className="max-w-2xl">
        <h2 className="text-2xl font-display font-bold">Portfolio health</h2>
        <p className="text-sm text-slate-400 mt-1.5">
          Realized margin vs. target for every active account, from the fixed rate card each
          customer was actually quoted against &mdash; not recalculated against today&apos;s buy
          cost. Click an account to see its full trend. All data is synthetic/illustrative.
        </p>
      </div>

      <PortfolioSummaryCards latestRows={latestRows} />

      <div className="mt-8">
        <AccountHealthTable customers={customers} summary={summary} />
      </div>

      <p className="text-xs text-slate-400 mt-4">
        * fewer than 8 shipments that month &mdash; read the realized margin with more caution than a
        full-volume month.
      </p>
    </div>
  );
}
