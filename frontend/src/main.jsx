/**
 * main.jsx — Application Entry Point
 * ====================================
 * This is the first JavaScript file that runs. It mounts the React app
 * into the <div id="root"> in index.html.
 *
 * LEARNING:
 *   React.StrictMode wraps the app and enables extra development warnings.
 *   It highlights potential problems like:
 *     - Deprecated lifecycle methods
 *     - Unexpected side effects
 *   It only runs in development mode — no performance impact in production.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// createRoot is React 18's way of mounting an app.
// It replaces the old ReactDOM.render() from React 17.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
