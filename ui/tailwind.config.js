/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        logo: ['"Big Shoulders Inline Text"', 'cursive'],
        body: ['"Inclusive Sans"', 'sans-serif'],
        mono: ['"Space Mono"', 'monospace'],
        samara: ['"Comfortaa"', 'cursive'],
        artery: ['"VT323"', 'monospace'],
      },
      colors: {
        background: '#0E0E10',
        surface: '#1A1A1C',
        border: '#2A2A2C',
        'samara-warm': '#D4A373',
        'artery-green': '#00FF00',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'typewriter': 'typewriter 0.05s steps(1) forwards',
        'breathing': 'breathing 3s ease-in-out infinite',
        'terminal-blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        pulseGlow: { '0%, 100%': { opacity: '0.4' }, '50%': { opacity: '0.8' } },
        typewriter: { '0%': { width: '0' }, '100%': { width: '100%' } },
        breathing: { '0%, 100%': { transform: 'scale(1)' }, '50%': { transform: 'scale(1.05)' } },
        blink: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0' } },
      },
    },
  },
  plugins: [],
};
