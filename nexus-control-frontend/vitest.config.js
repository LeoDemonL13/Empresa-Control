import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

                                                                                
                                                                             
                                  
export default defineConfig({
  plugins: [react()],
  test: {
                                                                               
                                                                      
    env: { TZ: 'America/Mexico_City' },
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    include: ['src/**/*.test.{js,jsx}'],
    css: false,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/**/*.test.{js,jsx}', 'src/test/**'],
    },
  },
})
