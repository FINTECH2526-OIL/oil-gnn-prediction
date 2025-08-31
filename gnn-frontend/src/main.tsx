import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

/**
 * Main entry point for the React application
 * 
 * This file:
 * - Renders the root App component
 * - Applies global CSS styles including Tailwind
 * - Uses React 18's createRoot API for better performance
 * - Wraps in StrictMode for development warnings
 */

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)