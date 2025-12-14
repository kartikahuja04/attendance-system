/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Institutional color palette - minimal and professional
        primary: '#4f46e5',      // Indigo - used sparingly
        'primary-hover': '#4338ca',
        background: '#f5f5f5',   // Light gray background
        card: '#ffffff',         // White cards
        border: '#e5e7eb',       // Light gray borders
        'text-primary': '#1f2937',   // Dark gray text
        'text-secondary': '#6b7280', // Medium gray text
        success: '#16a34a',      // Green
        warning: '#d97706',      // Amber
        error: '#dc2626',        // Red
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
