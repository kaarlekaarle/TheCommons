import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // USWDS-inspired color palette
        primary: {
          50: '#eef5ff',
          100: '#dbe9ff',
          200: '#bad3ff',
          300: '#8fb7ff',
          400: '#5f97f7',
          500: '#2f6fe6',
          600: '#1f54b5',
          700: '#183f87',
          800: '#122e63',
          900: '#0e244e',
        },
        success: {
          50: '#eefcf4',
          100: '#d6f7e4',
          200: '#a9eecc',
          300: '#74e1b0',
          400: '#3cca93',
          500: '#16a34a',
          600: '#148343',
          700: '#0f6336',
          800: '#0c4a2f',
          900: '#093b27',
        },
        accent: {
          500: '#f59e0b', // Sparingly used
        },
        neutral: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1f2937',
          900: '#0f172a',
        },

        // Custom gray scale for better contrast
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#4b5563', // Darker for better contrast (was #6b7280)
          600: '#4b5563', // Darker for better contrast
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },

        // Legacy Civic UI colors (keeping for compatibility)
        civic: {
          // Core semantic colors
          ink: '#1b1b1b', // Primary text
          'muted-ink': '#4b5563', // Secondary text
          canvas: '#f7f7f7', // Page background
          surface: '#ffffff', // Card background
          border: '#e5e7eb', // Lines and borders
          brand: '#0b6fbf', // Actions and links
          'brand-hover': '#095b99', // Brand hover state

          // Status colors
          success: '#2e7d32', // Success green
          warning: '#c77700', // Warning orange
          danger: '#b3261e', // Danger red

          // Level-specific colors
          levelA: '#0b6fbf', // Blue for Level A (Principles)
          levelB: '#1b7f5f', // Teal/green for Level B (Actions)
        },

        // Legacy gov colors (keeping for compatibility)
        gov: {
          primary: '#002f6c', // Navy blue
          secondary: '#f1c40f', // Muted gold
          background: '#f8f9fa', // Light neutral
          text: '#212529', // Dark gray
          'text-muted': '#495057', // Darker gray for better contrast (was #6c757d)
          'surface': '#ffffff', // White
          'border': '#dee2e6', // Light gray border
          'border-dark': '#adb5bd', // Darker border
          'success': '#28a745', // Government green
          'warning': '#ffc107', // Government yellow
          'danger': '#dc3545', // Government red
          'info': '#17a2b8', // Government blue
        },

        'primary-foreground': '#ffffff',

        // Background colors
        bg: {
          50: '#f8f9fa', // gov-background
          100: '#e9ecef',
          200: '#dee2e6',
          300: '#ced4da',
          400: '#adb5bd',
          500: '#495057', // Darker gray for better contrast (was #6c757d)
          600: '#495057',
          700: '#343a40',
          800: '#212529', // gov-text
          900: '#1a1d20',
        },

        // Surface colors
        surface: {
          50: '#ffffff', // gov-surface
          100: '#f8f9fa',
          200: '#e9ecef',
          300: '#dee2e6',
          400: '#ced4da',
          500: '#adb5bd',
          600: '#495057', // Darker gray for better contrast (was #6c757d)
          700: '#495057',
          800: '#343a40',
          900: '#212529',
          DEFAULT: '#ffffff',
        },

        // Border colors
        border: {
          50: '#f8fafc',
          100: '#e9ecef',
          200: '#dee2e6', // gov-border
          300: '#ced4da',
          400: '#adb5bd', // gov-border-dark
          500: '#495057', // Darker gray for better contrast (was #6c757d)
          600: '#495057',
          700: '#343a40',
          800: '#212529',
          900: '#1a1d20',
          DEFAULT: '#dee2e6',
        },

        // Muted colors
        muted: {
          50: '#f8fafc',
          100: '#e9ecef',
          200: '#dee2e6',
          300: '#ced4da',
          400: '#adb5bd',
          500: '#495057', // Darker gray for better contrast (was #6c757d)
          600: '#495057',
          700: '#343a40',
          800: '#212529',
          900: '#1a1d20',
          DEFAULT: '#495057', // Darker gray for better contrast (was #6c757d)
        },



        // Warning - Government yellow
        warning: {
          50: '#fff8e1',
          100: '#ffecb3',
          200: '#ffe082',
          300: '#ffd54f',
          400: '#ffca28',
          500: '#ffc107', // gov-warning
          600: '#ffb300',
          700: '#ffa000',
          800: '#ff8f00',
          900: '#ff6f00',
          DEFAULT: '#ffc107',
        },

        // Danger - Government red
        danger: {
          50: '#f8d7da',
          100: '#f5c6cb',
          200: '#f1b0b7',
          300: '#ec9aa3',
          400: '#e7848f',
          500: '#dc3545', // gov-danger
          600: '#c82333',
          700: '#a71e2a',
          800: '#861921',
          900: '#651418',
          DEFAULT: '#dc3545',
        },

        // Info - Government blue
        info: {
          50: '#d1ecf1',
          100: '#bee5eb',
          200: '#abdde4',
          300: '#98d5dd',
          400: '#85cdd6',
          500: '#17a2b8', // gov-info
          600: '#138496',
          700: '#0f6674',
          800: '#0b4852',
          900: '#072a30',
          DEFAULT: '#17a2b8',
        },
      },
      borderRadius: {
        // USWDS-inspired border radius scale
        'xs': '2px',
        'sm': '4px',
        'md': '8px', // Primary card radius
        'lg': '12px', // Secondary card radius
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
      },
      fontFamily: {
        sans: ['system-ui', 'ui-sans-serif', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      fontSize: {
        // USWDS-inspired typography scale
        'xs': ['0.75rem', { lineHeight: '1.1' }], // 12px
        'sm': ['0.875rem', { lineHeight: '1.45' }], // 14px
        'base': ['1rem', { lineHeight: '1.75' }], // 16px - body text
        'lg': ['1.125rem', { lineHeight: '1.55' }], // 18px
        'xl': ['1.25rem', { lineHeight: '1.5' }], // 20px
        '2xl': ['1.5rem', { lineHeight: '1.4' }], // 24px - H3
        '3xl': ['1.875rem', { lineHeight: '1.3' }], // 30px - H2
        '4xl': ['2.25rem', { lineHeight: '1.25' }], // 36px - H1
        '5xl': ['3rem', { lineHeight: '1.2' }], // 48px
        '6xl': ['3.75rem', { lineHeight: '1.1' }], // 60px
        'h1': ['clamp(2.25rem, 2.2vw + 1.5rem, 3rem)', { lineHeight: '1.2' }],
        'h2': ['2rem', { lineHeight: '1.3' }],
        'h3': ['1.5rem', { lineHeight: '1.4' }],
        'title': ['1.75rem', { lineHeight: '1.2' }],
        'eyebrow': ['0.8125rem', { lineHeight: '1.1' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
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
      boxShadow: {
        // USWDS-inspired shadows
        'card': '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'card-md': '0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)',
        'card-lg': '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
        'card-xl': '0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)',

        // Legacy shadows (keeping for compatibility)
        'civic': '0 1px 2px rgba(0, 0, 0, 0.05)',
        'civic-md': '0 2px 4px rgba(0, 0, 0, 0.08)',
        'civic-lg': '0 4px 8px rgba(0, 0, 0, 0.1)',
        'civic-xl': '0 8px 16px rgba(0, 0, 0, 0.12)',
        'gov': '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'gov-md': '0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)',
        'gov-lg': '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
        'gov-xl': '0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
