import { getSupabase } from "@/lib/supabase";
import QuoteCalculatorClient from "@/components/QuoteCalculatorClient";
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

export const revalidate = 0; // always read live data — this is a demo/portfolio dashboard, not high traffic

export default async function QuotePage() {
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

  const [lanesR, carriersR, serviceLevelsR, carrierRatesR, fuelLevyR, accessorialsR, customersR, rateCardsR] =
    await Promise.all([
      supabase.from("lanes").select("*").order("lane_id"),
      supabase.from("carriers").select("*"),
      supabase.from("service_levels").select("*"),
      supabase.from("carrier_rates").select("*"),
      supabase.from("fuel_levy_index").select("*").order("month"),
      supabase.from("accessorials").select("*"),
      supabase.from("customers").select("*").order("customer_name"),
      supabase.from("customer_rate_cards").select("*"),
    ]);

  const firstError = [lanesR, carriersR, serviceLevelsR, carrierRatesR, fuelLevyR, accessorialsR, customersR, rateCardsR].find(
    (r) => r.error
  )?.error;

  if (firstError) {
    return (
      <div className="mt-10 card p-6 border-rust/40">
        <h2 className="font-display font-bold text-lg text-rust">Couldn&apos;t load reference data</h2>
        <p className="text-sm text-slate-400 mt-2 font-mono">{firstError.message}</p>
        <p className="text-sm text-slate-400 mt-3">
          Check that the schema and seed SQL have been applied in Supabase, and that
          NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY are set correctly.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-6 sm:mt-10">
      <div className="max-w-2xl">
        <h2 className="text-2xl font-display font-bold">Quote a lane</h2>
        <p className="text-sm text-slate-400 mt-1.5">
          Prices a shipment the way a pricing analyst would: chargeable weight, live fuel levy,
          accessorials, then either the customer&apos;s existing fixed rate card or a default markup
          for a new prospect. Carrier is auto-selected as the cheapest eligible option for this
          lane/service/weight. All figures are synthetic/illustrative.
        </p>
      </div>
      <QuoteCalculatorClient
        lanes={(lanesR.data as Lane[]) ?? []}
        carriers={(carriersR.data as Carrier[]) ?? []}
        serviceLevels={(serviceLevelsR.data as ServiceLevel[]) ?? []}
        carrierRates={(carrierRatesR.data as CarrierRate[]) ?? []}
        fuelLevyIndex={(fuelLevyR.data as FuelLevyMonth[]) ?? []}
        accessorials={(accessorialsR.data as Accessorial[]) ?? []}
        customers={(customersR.data as Customer[]) ?? []}
        customerRateCards={(rateCardsR.data as CustomerRateCard[]) ?? []}
      />
    </div>
  );
}
