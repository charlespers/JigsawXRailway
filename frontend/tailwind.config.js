/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'neon-teal': '#00d4b8', // Reduced saturation ~25%
        'electric-orange': '#e55a2b', // Reduced saturation ~20%
        'neutral-blue': '#5b8fa8', // Desaturated blue for secondary actions
        'dark-bg': '#0a0a0a',
        'dark-surface': '#111114',
        'dark-border': '#1d1d22',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'circuit-grid': 'linear-gradient(rgba(0, 255, 209, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 209, 0.03) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
    },
  },
  plugins: [],
}

