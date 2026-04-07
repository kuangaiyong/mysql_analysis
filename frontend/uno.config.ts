import { defineConfig, presetUno, presetAttributify, presetWind3 } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetWind3()
  ],
  theme: {
    colors: {
      primary: '#3b82f6',
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444'
    }
  }
})
