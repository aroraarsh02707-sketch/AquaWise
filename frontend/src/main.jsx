import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const fontPreload = document.getElementById('aqua-font-preload');
if (fontPreload instanceof HTMLLinkElement) {
  const fontStylesheet = document.createElement('link');
  fontStylesheet.rel = 'stylesheet';
  fontStylesheet.href = fontPreload.href;
  fontStylesheet.media = 'print';
  fontStylesheet.addEventListener('load', () => { fontStylesheet.media = 'all'; }, { once: true });
  document.head.appendChild(fontStylesheet);
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
