import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0ea5e9',
        'primary-foreground': '#06141a',
        bg: '#0b1115',
        surface: '#121a21',
        border: '#1f2a33',
        muted: '#64748b',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
      },
      borderRadius: {
        lg: '16px',
        md: '12px',
        sm: '8px',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      container: {
        center: true,
        padding: '1rem',
        screens: {
          md: '704px',
          lg: '976px',
          xl: '1200px',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
