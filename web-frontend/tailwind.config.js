/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Indian flag-inspired palette
        saffron: { DEFAULT: "#FF9933", 50: "#FFF4E6", 100: "#FFE0B3" },
        govgreen: { DEFAULT: "#138808", 50: "#E6F4E5", 100: "#C2E5BF" },
        ashok: { DEFAULT: "#000080" },
      },
      fontFamily: {
        sans: ["'Noto Sans'", "'Noto Sans Devanagari'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
