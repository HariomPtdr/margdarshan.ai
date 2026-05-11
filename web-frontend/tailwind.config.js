/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Primary brand — charcoal (from jet page)
        brand:    { DEFAULT: "#202A36", dark: "#1a2229", light: "#2d3a4a" },
        // Legacy (keep for backward compat)
        saffron:  { DEFAULT: "#FF9933", 50: "#FFF4E6", 100: "#FFE0B3" },
        govgreen: { DEFAULT: "#138808", 50: "#E6F4E5" },
        ashok:    { DEFAULT: "#202A36" },
        // Surfaces
        surface:  { DEFAULT: "#F9FAFB", card: "#FFFFFF", subtle: "#F3F4F6" },
        // Text
        ink:      { DEFAULT: "#111827", muted: "#6B7280", light: "#9CA3AF" },
      },
      fontFamily: {
        sans: ["'Inter'", "'Noto Sans'", "'Noto Sans Devanagari'", "system-ui", "sans-serif"],
      },
      letterSpacing: { tightest: "-0.04em" },
      boxShadow: {
        card:  "0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
        float: "0 8px 32px rgba(0,0,0,0.10)",
        nav:   "0 1px 0 rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};
