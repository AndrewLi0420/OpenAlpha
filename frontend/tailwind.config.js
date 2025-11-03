/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Financial blue accents
        'financial-blue': {
          light: '#00D4FF',
          DEFAULT: '#0EA5E9',
          dark: '#0284C7',
        },
        // Financial green accents
        'financial-green': {
          light: '#22C55E',
          DEFAULT: '#10B981',
          dark: '#059669',
        },
      },
      fontFamily: {
        // System font stack for body text
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'sans-serif'],
        // Monospace for numerical data
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};

