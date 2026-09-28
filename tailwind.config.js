/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  safelist: ["form-input", "form-select", "form-input-error"],
  theme: {
    extend: {
      colors: {
        // Luxury gold scale (used for accents, buttons, hover-glows)
        gold: {
          200: "#fbe8b6",
          300: "#f5d97c",
          400: "#e9c04d",
          500: "#d4a72c",
          600: "#b8891f",
          700: "#8f6a15",
        },
        // Near-black "carbon" surface palette
        nv: {
          950: "#07080b",  // page background
          900: "#0c0e13",  // raised surface
          850: "#12151c",  // card
          800: "#171b23",  // hover surface
          700: "#202530",  // borders / dividers
          600: "#2c333f",
          500: "#8b93a3",  // muted text
          400: "#a8afbd",  // secondary text
          300: "#c7cdd8",  // body text
          200: "#e2e5ec",  // headings
          100: "#f3f4f7",  // near-white text
        },
      },
      fontFamily: {
        display: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        gold: "0 0 24px rgba(212, 167, 44, 0.35)",
        "gold-lg": "0 8px 40px rgba(212, 167, 44, 0.45)",
        glass: "inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 12px 32px -12px rgba(0, 0, 0, 0.55)",
        "card-glow": "0 0 0 1px rgba(217, 180, 80, 0.0), 0 18px 48px -18px rgba(0,0,0,0.8)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};