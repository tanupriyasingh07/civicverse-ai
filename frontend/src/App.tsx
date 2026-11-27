import { useEffect, useState } from 'react';
import { systemApi } from './services/api';

function App() {
  const [backendStatus, setBackendStatus] = useState<string>('Checking backend...');

  useEffect(() => {
    systemApi
      .health()
      .then((data) => setBackendStatus(Online ( :)))
      .catch(() => setBackendStatus('Offline (Start FastAPI on port 8001)'));
  }, []);

  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center bg-slate-950 text-slate-100">
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-8 text-center shadow-2xl">
        <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-amber-400">
          Urban Digital Twin • v0.1
        </span>
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-white">CivicVerse AI</h1>
        <p className="mt-2 text-sm text-slate-400">
          Multi-Agent Urban Crisis Simulation & Decision Intelligence Platform
        </p>
        <div className="mt-6 rounded-lg border border-slate-800 bg-slate-950 px-4 py-2 text-xs font-mono text-emerald-400">
          Backend Link: {backendStatus}
        </div>
      </div>
    </div>
  );
}

export default App;
