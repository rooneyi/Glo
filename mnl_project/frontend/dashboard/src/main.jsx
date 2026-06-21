import React from 'react';
import { createRoot } from 'react-dom/client';
import Dashboard from './Dashboard';

const el = document.getElementById('dashboard-root');
const dataEl = document.getElementById('dashboard-data');

if (el && dataEl) {
  const payload = JSON.parse(dataEl.textContent);
  createRoot(el).render(
    <React.StrictMode>
      <div data-dashboard-mounted="">
        <Dashboard data={payload} />
      </div>
    </React.StrictMode>,
  );
  document.getElementById('dashboard-skeleton')?.remove();
}
