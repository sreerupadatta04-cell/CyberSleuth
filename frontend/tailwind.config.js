/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: "#091315",
        charcoal: "#101C1D",
        teal: {
          DEFAULT: "#033C42",
          brand: "#033C42",
          dark: "#022B2F",
          light: "#055861",
        },
        cyan: {
          neon: "#00D5C5",
        },
        lime: {
          acid: "#B6FF5C",
        },
        amber: {
          neon: "#FFB454",
        },
        coral: {
          neon: "#FF626C",
        },
        ivory: "#E7F0EC",
        sage: "#91AAA5",
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'monospace'],
        heading: ['"Space Grotesk"', 'sans-serif'],
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'neon-cyan': '0 0 15px -3px rgba(0, 213, 197, 0.3)',
        'neon-lime': '0 0 15px -3px rgba(182, 255, 92, 0.3)',
        'neon-coral': '0 0 15px -3px rgba(255, 98, 108, 0.3)',
        'panel': '0 4px 20px -2px rgba(9, 19, 21, 0.7), 0 0 0 1px rgba(0, 213, 197, 0.1)',
      },
      backgroundImage: {
        'grid-pattern': "radial-gradient(rgba(0, 213, 197, 0.08) 1px, transparent 1px)",
      }
    },
  },
  plugins: [],
}
