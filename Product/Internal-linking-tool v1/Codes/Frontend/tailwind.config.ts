import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f6f8fb",
        foreground: "#172033",
        muted: "#667085",
        panel: "#ffffff",
        panelAlt: "#f1f5f9",
        border: "#d9e1ec",
        accent: "#0f766e",
        accentSoft: "#ecfdf5",
        accentAlt: "#2563eb",
        danger: "#b42318",
        warning: "#b45309",
        success: "#15803d",
      },
      boxShadow: {
        panel: "0 18px 45px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
