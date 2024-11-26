import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './main.css';
import './i18n';
import { initializeApp } from './utils/initializeApp';

// 初始化应用
initializeApp();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
