/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          DEFAULT: "#004532",
          dark: "#003224",
          light: "#055c44",
        },
        emerald: {
          DEFAULT: "#065f46",
          dark: "#044734",
          light: "#0a8160",
        },
        mint: {
          DEFAULT: "#10b981",
          light: "#34d399",
          dark: "#059669",
        },
        amber: {
          DEFAULT: "#fe932c",
          dark: "#d97706",
          light: "#fbb066",
        },
        canvas: "#faf9f5",
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
