import { ref } from 'vue'

export type Theme = 'deep-space' | 'cyberpunk' | 'chatgpt-white' | 'fresh-green' | 'black-gold' | 'red-black'

const currentTheme = ref<Theme>('deep-space')

const themes: Record<Theme, Record<string, string>> = {
  'deep-space': {
    '--bg-gradient-start': '#0f172a',
    '--bg-gradient-end': '#1a2a6c',
    '--primary-color': '#d4af37',
    '--text-color': '#ffffff',
    '--glass-bg': 'rgba(15, 23, 42, 0.7)',
    '--glass-border': 'rgba(212, 175, 55, 0.3)',
    '--card-hover-shadow': '0 10px 30px rgba(0, 0, 0, 0.5)',
    '--accent-glow': 'rgba(212, 175, 55, 0.2)'
  },
  'cyberpunk': {
    '--bg-gradient-start': '#050505',
    '--bg-gradient-end': '#1a0b2e',
    '--primary-color': '#00f3ff',
    '--text-color': '#fff0f5',
    '--glass-bg': 'rgba(20, 10, 30, 0.8)',
    '--glass-border': 'rgba(0, 243, 255, 0.5)',
    '--card-hover-shadow': '0 0 20px rgba(0, 243, 255, 0.4)',
    '--accent-glow': 'rgba(255, 0, 85, 0.3)'
  },
  'chatgpt-white': {
    '--bg-gradient-start': '#ffffff',
    '--bg-gradient-end': '#f7f7f8',
    '--primary-color': '#10a37f',
    '--text-color': '#2d3748',
    '--glass-bg': 'rgba(255, 255, 255, 0.9)',
    '--glass-border': 'rgba(0, 0, 0, 0.1)',
    '--card-hover-shadow': '0 4px 12px rgba(0, 0, 0, 0.1)',
    '--accent-glow': 'rgba(16, 163, 127, 0.1)'
  },
  'fresh-green': {
    '--bg-gradient-start': '#e0f7fa',
    '--bg-gradient-end': '#e8f5e9',
    '--primary-color': '#4caf50',
    '--text-color': '#37474f',
    '--glass-bg': 'rgba(255, 255, 255, 0.6)',
    '--glass-border': 'rgba(76, 175, 80, 0.3)',
    '--card-hover-shadow': '0 8px 24px rgba(76, 175, 80, 0.2)',
    '--accent-glow': 'rgba(76, 175, 80, 0.2)'
  },
  'black-gold': {
    '--bg-gradient-start': '#000000',
    '--bg-gradient-end': '#1c1c1c',
    '--primary-color': '#ffd700',
    '--text-color': '#ffffff',
    '--glass-bg': 'rgba(20, 20, 20, 0.9)',
    '--glass-border': 'rgba(255, 215, 0, 0.3)',
    '--card-hover-shadow': '0 10px 30px rgba(255, 215, 0, 0.15)',
    '--accent-glow': 'rgba(255, 215, 0, 0.1)'
  },
  'red-black': {
    '--bg-gradient-start': '#1a0505',
    '--bg-gradient-end': '#000000',
    '--primary-color': '#ff3333',
    '--text-color': '#ffffff',
    '--glass-bg': 'rgba(40, 10, 10, 0.85)',
    '--glass-border': 'rgba(255, 51, 51, 0.4)',
    '--card-hover-shadow': '0 10px 30px rgba(255, 51, 51, 0.25)',
    '--accent-glow': 'rgba(255, 51, 51, 0.2)'
  }
}

export function useTheme() {
  const applyTheme = (theme: Theme) => {
    const root = document.documentElement
    const themeVars = themes[theme]
    
    for (const [key, value] of Object.entries(themeVars)) {
      root.style.setProperty(key, value)
    }
    currentTheme.value = theme
  }

  // Initialize
  applyTheme(currentTheme.value)

  return {
    currentTheme,
    applyTheme,
    availableThemes: Object.keys(themes) as Theme[]
  }
}
