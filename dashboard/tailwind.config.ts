import type { Config } from "tailwindcss";

// Design tokens for the Freight Pricing & Margin dashboard.
// Palette: a "shipping manifest / ledger" theme -- deep ink navy chrome,
// cool muted paper (not cream), and three signal colors doing real work
// (margin ok / warning / breach) rather than one decorative accent.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#101826",
          800: "#182233",
          700: "#242F42",
        },
        slate: {
          DEFAULT: "#3C4A5E",
          400: "#6B7A8F",
        },
        paper: {
          DEFAULT: "#EEF0EA",
          card: "#FFFFFF",
        },
        line: "#D8DCD2",
        rust: { DEFAULT: "#B8441F", soft: "#F3DED4" },
        amber: { DEFAULT: "#A9740A", soft: "#F1E6C8" },
        pine: { DEFAULT: "#2E5F45", soft: "#DCE8DF" },
        route: { DEFAULT: "#1F6E8C", soft: "#D9E8ED" },
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-plex-sans)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
      backgroundImage: {
        "dotted-line": "repeating-linear-gradient(90deg, #B8C0B0 0, #B8C0B0 4px, transparent 4px, transparent 10px)",
      },
    },
  },
  plugins: [],
};
export default config;
