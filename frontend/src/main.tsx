import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// IBM Plex Mono — monospace z charakterem, pasuje do danych naukowych
const link = document.createElement('link')
link.rel = 'stylesheet'
link.href = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap'
document.head.appendChild(link)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
