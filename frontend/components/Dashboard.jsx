"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-4xl font-extrabold text-slate-800 mt-1">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

function ToggleSwitch({ enabled, onChange, loading }) {
  return (
    <button
      onClick={() => !loading && onChange(!enabled)}
      className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-300
        focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500
        ${enabled ? "bg-indigo-500" : "bg-slate-200"}
        ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
      aria-pressed={enabled}
    >
      <span className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md
        transition-transform duration-300 ${enabled ? "translate-x-7" : "translate-x-1"}`} />
    </button>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-7">
      <h2 className="text-lg font-bold text-slate-800 mb-5">{title}</h2>
      {children}
    </div>
  );
}

export default function Dashboard({ tenantId }) {
  const [aiMode,        setAiMode]        = useState(true);
  const [toggling,      setToggling]      = useState(false);
  const [activeCallSid, setActiveCallSid] = useState(null);
  const [metrics,       setMetrics]       = useState({
    totalCalls: 0, aiHandled: 0, avgDuration: "0:00", ordersToday: 0,
  });
  const [phoneConfig, setPhoneConfig] = useState({ twilioNumber: "", ownerPhone: "" });
  const [saveStatus,  setSaveStatus]  = useState("");

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res  = await fetch(`${API}/dashboard/${tenantId}/metrics`);
        if (!res.ok) return;
        const data = await res.json();
        setMetrics(data.metrics);
        setPhoneConfig(data.phone_config);
        setAiMode(data.ai_mode_enabled);
        setActiveCallSid(data.active_call_sid ?? null);
      } catch (e) { console.error("Metrics fetch failed", e); }
    };
    fetchMetrics();
    const id = setInterval(fetchMetrics, 30_000);
    return () => clearInterval(id);
  }, [tenantId]);

  const handleToggle = async (newValue) => {
    setToggling(true);
    try {
      const res = await fetch(`${API}/telephony/toggle-mode/${tenantId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: newValue ? "AI" : "LIVE_PERSON",
          active_call_sid: activeCallSid,
        }),
      });
      if (res.ok) setAiMode(newValue);
    } catch (e) { console.error("Toggle failed", e); }
    finally    { setToggling(false); }
  };

  const handleSaveConfig = async () => {
    setSaveStatus("saving");
    try {
      await fetch(`${API}/dashboard/${tenantId}/phone-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(phoneConfig),
      });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(""), 2000);
    } catch { setSaveStatus("error"); }
  };

  const automationRate = metrics.totalCalls > 0
    ? Math.round((metrics.aiHandled / metrics.totalCalls) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-slate-50 p-8 max-w-5xl mx-auto">
      <div className="mb-10">
        <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">🌲 Pine Sales AI</h1>
        <p className="text-slate-400 text-sm mt-1">Business Control Panel — {tenantId}</p>
      </div>

      {/* AI / Live toggle */}
      <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-7 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-800">Call Routing Mode</h2>
            <p className="text-sm text-slate-400 mt-0.5">
              {aiMode ? "AI Agent is answering calls automatically." : "Calls forwarded directly to you."}
            </p>
            {activeCallSid && (
              <span className="inline-block mt-2 text-xs font-medium bg-amber-100 text-amber-700 px-3 py-1 rounded-full">
                📞 Active call in progress
              </span>
            )}
          </div>
          <div className="flex flex-col items-center gap-1">
            <ToggleSwitch enabled={aiMode} onChange={handleToggle} loading={toggling} />
            <span className="text-xs font-semibold text-slate-500">
              {aiMode ? "AI Mode" : "Live Person"}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <StatCard label="Total Calls Today"  value={metrics.totalCalls} />
        <StatCard label="AI Handled"         value={metrics.aiHandled}
                  sub={`${automationRate}% automation rate`} />
        <StatCard label="Avg. Duration"      value={metrics.avgDuration} />
        <StatCard label="Orders Placed"      value={metrics.ordersToday} sub="via AI today" />
      </div>

      {/* Phone Config */}
      <Section title="Phone Configuration">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {[
            { label: "Twilio Number (AI Line)", key: "twilioNumber", placeholder: "+1 (555) 000-0000" },
            { label: "Owner / Fallback Phone",  key: "ownerPhone",   placeholder: "+1 (555) 111-2222" },
          ].map(({ label, key, placeholder }) => (
            <div key={key}>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">
                {label}
              </label>
              <input
                type="tel"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3
                           text-slate-700 placeholder-slate-300 focus:outline-none
                           focus:ring-2 focus:ring-indigo-300 transition"
                placeholder={placeholder}
                value={phoneConfig[key] || ""}
                onChange={e => setPhoneConfig(prev => ({ ...prev, [key]: e.target.value }))}
              />
            </div>
          ))}
        </div>
        <button
          onClick={handleSaveConfig}
          disabled={saveStatus === "saving"}
          className="mt-6 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-60 text-white font-bold
                     px-6 py-3 rounded-2xl transition-colors shadow-md shadow-indigo-100 active:scale-95"
        >
          {saveStatus === "saving" ? "Saving…" : saveStatus === "saved" ? "✓ Saved!" : "Save Configuration"}
        </button>
      </Section>

      {/* Quick link to kitchen */}
      <div className="mt-6 text-center">
        <a href={`/kitchen/${tenantId}`}
           className="text-sm text-indigo-500 hover:underline font-medium">
          → Open Kitchen Monitor for this location
        </a>
      </div>
    </div>
  );
}
