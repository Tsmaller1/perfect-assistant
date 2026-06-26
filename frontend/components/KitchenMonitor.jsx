"use client";

import { useEffect, useRef, useState, useCallback } from "react";

const WS_URL = process.env.NEXT_PUBLIC_KDS_WS_URL || "ws://localhost:8000";
const RECONNECT_DELAY_MS = 3000;

function ElapsedTimer({ receivedAt }) {
  const [elapsed, setElapsed] = useState("0:00");
  const [isLate, setIsLate]   = useState(false);

  useEffect(() => {
    const start = new Date(receivedAt).getTime();
    const tick  = () => {
      const diff = Math.floor((Date.now() - start) / 1000);
      const m    = Math.floor(diff / 60);
      const s    = String(diff % 60).padStart(2, "0");
      setElapsed(`${m}:${s}`);
      setIsLate(m >= 10);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [receivedAt]);

  return (
    <span className={`font-mono text-sm font-semibold ${isLate ? "text-red-500 animate-pulse" : "text-amber-500"}`}>
      ⏱ {elapsed}
    </span>
  );
}

function TicketCard({ ticket, onComplete }) {
  return (
    <div className="bg-white rounded-3xl shadow-lg border border-slate-100 p-5 flex flex-col gap-3 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">
            Order #{(ticket.order_id || "00000").slice(-5).toUpperCase()}
          </p>
          <h2 className="text-xl font-bold text-slate-800 mt-0.5">{ticket.customer_name}</h2>
          {ticket.customer_phone && (
            <p className="text-xs text-slate-400">{ticket.customer_phone}</p>
          )}
        </div>
        <ElapsedTimer receivedAt={ticket.received_at} />
      </div>

      <ul className="divide-y divide-slate-100">
        {(ticket.items || []).map((item, idx) => (
          <li key={idx} className="py-2">
            <span className="font-semibold text-slate-700">
              {item.quantity}x {item.name}
            </span>
            {item.customization && (
              <p className="text-xs text-slate-500 mt-0.5 italic">— {item.customization}</p>
            )}
          </li>
        ))}
      </ul>

      {ticket.special_instructions && (
        <div className="bg-amber-50 rounded-2xl px-4 py-2 text-sm text-amber-800">
          📝 {ticket.special_instructions}
        </div>
      )}

      <button
        onClick={() => onComplete(ticket.order_id)}
        className="mt-1 w-full bg-emerald-500 hover:bg-emerald-600 active:scale-95
                   text-white font-bold py-3 rounded-2xl transition-all duration-150
                   shadow-md shadow-emerald-200"
      >
        ✓ Complete & Clear Ticket
      </button>
    </div>
  );
}

export default function KitchenMonitor({ tenantId }) {
  const [tickets,   setTickets]   = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef            = useRef(null);
  const reconnectTimer   = useRef(null);
  const audioRef         = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(`${WS_URL}/api/kds/${tenantId}/stream`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      clearTimeout(reconnectTimer.current);
      console.log("[KDS] Connected");
    };

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.event === "NEW_ORDER") {
        setTickets(prev => [data.ticket, ...prev]);
        audioRef.current?.play().catch(() => {});
      }
      if (data.event === "TICKET_UPDATE" && data.status === "COMPLETE") {
        setTickets(prev => prev.filter(t => t.order_id !== data.order_id));
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.warn("[KDS] Disconnected — reconnecting in 3s…");
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = (err) => { console.error("[KDS] Error", err); ws.close(); };
  }, [tenantId]);

  useEffect(() => {
    connect();
    return () => { clearTimeout(reconnectTimer.current); wsRef.current?.close(); };
  }, [connect]);

  const handleComplete = useCallback((orderId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event: "COMPLETE_TICKET", order_id: orderId }));
    }
    setTickets(prev => prev.filter(t => t.order_id !== orderId));
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      {/* Invisible audio alert — drop a chime file at /public/sounds/order-alert.mp3 */}
      <audio ref={audioRef} src="/sounds/order-alert.mp3" preload="auto" />

      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">🍕 Kitchen Display</h1>
        <span className={`inline-flex items-center gap-1.5 text-sm font-semibold px-4 py-1.5 rounded-full
          ${connected ? "bg-emerald-900/60 text-emerald-400" : "bg-red-900/60 text-red-400 animate-pulse"}`}>
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400" : "bg-red-400"}`} />
          {connected ? "Live" : "Reconnecting…"}
        </span>
      </div>

      {tickets.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-600 select-none">
          <span className="text-6xl">🧑‍🍳</span>
          <p className="mt-4 text-lg font-medium">No active orders</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {tickets.map(ticket => (
            <TicketCard key={ticket.order_id} ticket={ticket} onComplete={handleComplete} />
          ))}
        </div>
      )}
    </div>
  );
}
