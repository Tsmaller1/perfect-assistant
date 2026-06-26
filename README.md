# 🌲 Pine Sales AI

Multi-tenant B2B SaaS — AI Voice Agents + Real-Time Kitchen Display System (KDS)

---

## Project Structure

```
pine-sales-ai/
├── backend/
│   ├── main.py              # FastAPI app entry point + KDS WebSocket endpoint
│   ├── kds_manager.py       # WebSocket manager for kitchen monitors
│   ├── telephony_router.py  # Call routing, AI media stream, hot-transfer
│   ├── agent_engine.py      # AI agent session + tool definitions
│   ├── scraper.py           # Async Playwright website scraper
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── app/
    │   ├── layout.js
    │   ├── page.js                        # Home / nav
    │   ├── dashboard/[tenantId]/page.js
    │   └── kitchen/[tenantId]/page.js
    ├── components/
    │   ├── Dashboard.jsx    # Business Control Panel
    │   └── KitchenMonitor.jsx # Real-Time KDS Screen
    ├── package.json
    ├── tailwind.config.js
    ├── next.config.js
    └── .env.local.example
```

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env                               # Fill in your API keys
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local                  # Set API URLs
npm run dev
```

Open:
- **Dashboard**: http://localhost:3000/dashboard/demo-tenant
- **Kitchen Monitor**: http://localhost:3000/kitchen/demo-tenant

---

## Configuration

### Environment Variables — Backend (`.env`)

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for Whisper + GPT-4o + TTS |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |

### Environment Variables — Frontend (`.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend HTTP URL (e.g. http://localhost:8000) |
| `NEXT_PUBLIC_KDS_WS_URL` | Backend WebSocket URL (e.g. ws://localhost:8000) |

---

## Key Features

- **AI Voice Agent** answers inbound calls, takes orders, fires `submit_kitchen_order` tool call
- **Hot-Transfer** — operator flips dashboard toggle mid-call; live caller is bridged to owner's phone via Twilio REST, no drop
- **KDS WebSocket** — orders appear on kitchen monitor within milliseconds of AI completing the order
- **Auto-Reconnect** — kitchen monitor re-connects automatically after any network drop
- **Live Elapsed Timer** — each ticket shows time open; turns red after 10 minutes
- **Audio Alert** — browser plays a chime on every new ticket (place MP3 at `/public/sounds/order-alert.mp3`)

---

## Production Checklist

- [ ] Replace `_get_tenant_config()` stub with real DB (PostgreSQL + SQLAlchemy async recommended)
- [ ] Add JWT / API key auth middleware to all FastAPI endpoints
- [ ] Integrate a vector DB (Pinecone, pgvector, or Weaviate) in `scraper.py`
- [ ] Lock CORS origins to your production domain
- [ ] Deploy backend on Railway / Fly.io / AWS ECS; frontend on Vercel
- [ ] Add `/public/sounds/order-alert.mp3` chime file to frontend
- [ ] Set up Twilio webhook URL to point to `/telephony/incoming/{tenant_id}`
