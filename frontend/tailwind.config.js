/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: "#101216",
          900: "#181B21",
          800: "#22262E",
          700: "#2E333D",
          600: "#40474F",
        },
        signal: {
          amber: "#F2A93B", // recording / active state
          teal: "#3FD6C2",  // confidence / landmarks / success
          coral: "#F26B5B", // errors / low confidence
        },
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      animation: {
        "pulse-rec": "pulse-rec 1.6s ease-in-out infinite",
      },
      keyframes: {
        "pulse-rec": {
          "0%, 100%": { opacity: 1, transform: "scale(1)" },
          "50%": { opacity: 0.5, transform: "scale(0.85)" },
        },
      },
    },
  },
  plugins: [],
};
