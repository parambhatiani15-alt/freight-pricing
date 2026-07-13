import { createClient, SupabaseClient } from "@supabase/supabase-js";

// The client is created lazily (on first use) rather than at module load.
// Next.js imports every page while building, so a module-scope createClient
// with missing env vars would fail the whole build instead of surfacing the
// friendly config-error card the pages render at runtime.
let client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient | null {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    // Surfaced clearly at build/runtime rather than a silent undefined client --
    // saves the "why is my data blank" debugging loop.
    console.warn(
      "Supabase env vars are missing. Set NEXT_PUBLIC_SUPABASE_URL and " +
        "NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local (see .env.local.example)."
    );
    return null;
  }

  // A single client is fine here: this project only ever reads with the
  // public anon key against tables that are meant to be readable (illustrative
  // data, no auth). If you extend this with real customer data, add Row Level
  // Security policies before relying on the anon key this way.
  if (!client) {
    client = createClient(supabaseUrl, supabaseAnonKey);
  }
  return client;
}
