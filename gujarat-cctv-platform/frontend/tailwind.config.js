/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        police: {
          blue: '#1E3A5F',
          light: '#2A4D7C',
          dark: '#11223A'
        },
        saffron: {
          DEFAULT: '#FF6B35',
          light: '#FF8A5E',
          dark: '#E5511A'
        }
      }
    },
  },
  plugins: [],
}
