/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // TwelveLabs brand colors
        'tl-charcoal': '#1D1C1B',
        'tl-white': '#F4F3F3',
        'tl-light-grey': '#D3D1CF',
        'tl-medium-grey': '#9B9896',
        'tl-dark-grey': '#3A3938',
        'tl-blue': '#0066FF',
        'tl-green': '#00CC88',
        'tl-orange': '#FF6B35',
        'tl-purple': '#8B5CF6',
        'tl-pink': '#EC4899',
        'tl-cyan': '#06B6D4',
        'tl-yellow': '#FBBF24',
        'tl-red': '#EF4444',
        'tl-indigo': '#6366F1',
      },
      borderRadius: {
        'tl-xs': '1.2%',
        'tl-sm': '2.4%',
        'tl-md': '4%',
        'tl-lg': '8%',
        'tl-xl': '12%',
        'tl-2xl': '16%',
        'tl-3xl': '24%',
      },
    },
  },
  plugins: [],
}