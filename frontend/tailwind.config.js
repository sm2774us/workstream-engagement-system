/** Tailwind + Radix design-token bridge, per JD "Tailwind with Radix or Fluent UI". */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        wes: {
          bg: "#0b1220",
          panel: "#131c2e",
          accent: "#4f8cff",
          risk: "#ef4444",
          ok: "#22c55e",
        },
      },
    },
  },
  plugins: [],
};
