import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.tsx'

// Initialize Sentry if DSN is provided
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
const environment = import.meta.env.VITE_ENVIRONMENT || 'dev'

if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: environment,
    // BrowserTracing integration disabled due to React 19 compatibility issues
    // integrations: [
    //   new BrowserTracing({
    //     tracePropagationTargets: ['localhost', '127.0.0.1'],
    //   }),
    // ],
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
