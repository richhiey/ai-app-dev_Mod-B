import { defineConfig, loadEnv } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Only the dev-server process receives these. No VITE_ prefix or client define.
  const settings = loadEnv(mode, process.cwd(), 'FIELDCARE_')
  for (const name of ['FIELDCARE_SERVICE_URL', 'FIELDCARE_CALLER_KEY']) {
    if (process.env[name] === undefined && settings[name]) process.env[name] = settings[name]
  }
  return { plugins: [tanstackStart(), react()] }
})
