# Perfect Assistant — AI Receptionist Platform

**An intelligent phone system that helps any business accept calls, book appointments, qualify leads, and handle payments — powered by AI.**

---

## 🎯 What is Perfect Assistant?

Perfect Assistant is a **multi-tenant AI receptionist platform** that enables businesses to:

✅ **Accept & manage inbound calls** with AI handling the conversation  
✅ **Auto-learn business context** by scraping company websites  
✅ **Book appointments & reservations** without human intervention  
✅ **Take orders** and route to fulfillment systems  
✅ **Qualify leads** for sales teams  
✅ **Hand off to humans** seamlessly for payment processing  

---

## 🚀 Key Features

### 1. Website-to-AI Knowledge
Business submits website URL → AI automatically scrapes and learns services, pricing, hours, FAQs → AI uses this context to answer questions accurately.

### 2. Intelligent Call Handling
Customer calls → AI answers with business-specific greeting → Handles inquiries, books appointments, or takes orders → Transcribes automatically.

### 3. Multi-Action Support
- **Orders**: Take product/service orders, route to fulfillment
- **Appointments**: Schedule meetings, check availability
- **Leads**: Qualify potential customers for sales
- **Reservations**: Manage bookings

### 4. Seamless Handoff
When payment needed: Transfer to human → Lead created with full context → Admin dashboard shows it.

### 5. Real-Time Admin Dashboard
Overview of calls, appointments, orders, leads with real-time updates via WebSocket.

---

## 📁 Project Structure

```
perfect-assistant/
├── backend/
│   ├── main.py                    # FastAPI app + endpoints
│   ├── telephony_router.py        # Twilio call handling
│   ├── agent_engine.py            # AI conversation engine
│   ├── action_queue.py            # Multi-action queue (orders/apts/leads)
│   ├── scraper_enhanced.py        # Web scraper
│   ├── appointments.py            # Appointment management
│   ├── payment_handoff.py         # Payment handoff system
│   ├── conversation_memory.py     # Conversation storage & context
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── layout.js
│   │   ├── page.js
│   │   ├── dashboard/[tenantId]/page.js
│   │   └── kitchen/[tenantId]/page.js
│   ├── components/
│   │   ├── Dashboard.jsx
│   │   └── KitchenMonitor.jsx
│   ├── package.json
│   └── tailwind.config.js
│
├── docs/
│   ├── FEATURE_SPEC.md
│   ├── DATABASE_SCHEMA.md
│   └── WEB_SCRAPER_SPEC.md
│
├── DEPLOYMENT.md
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+, Node.js 16+, PostgreSQL
- Twilio & OpenAI accounts

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access:
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000/dashboard/tenant-1

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 📊 Core Modules

| Module | Purpose |
|--------|---------|
| `telephony_router.py` | Twilio webhook handling, WebSocket streaming |
| `agent_engine.py` | GPT-4o conversation engine with function tools |
| `action_queue.py` | Generalized action queue for orders/appointments/leads |
| `scraper_enhanced.py` | Website scraper to extract business context |
| `appointments.py` | Appointment booking & availability checking |
| `payment_handoff.py` | Payment transfers & lead qualification |
| `conversation_memory.py` | Conversation storage with entity extraction |

---

## 🔌 API Endpoints

```
POST   /api/businesses/{tenant_id}/onboard
GET    /api/businesses/{tenant_id}/profile
POST   /api/appointments/{tenant_id}/book
GET    /api/appointments/{tenant_id}/availability
GET    /api/leads/{tenant_id}
GET    /api/leads/{tenant_id}/qualified
PATCH  /api/leads/{tenant_id}/{lead_id}
GET    /api/actions/{tenant_id}
WS     /api/kds/{tenant_id}/stream
```

Full docs: http://localhost:8000/docs

---

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.9+
- **AI**: OpenAI GPT-4o
- **Phone**: Twilio SDK
- **Database**: PostgreSQL (or SQLite for dev)
- **Web Scraping**: BeautifulSoup + httpx
- **Frontend**: Next.js + React + Tailwind CSS

---

## 🎓 Use Cases

| Industry | Example |
|----------|---------|
| **Education** | "What courses do you offer?" → Books consultation → Lead created |
| **Healthcare** | "Can I schedule an appointment?" → Checks availability → Books appt |
| **E-Commerce** | "Can I place an order?" → Takes order → Routes to fulfillment |
| **Services** | "How much for web dev?" → Qualifies lead → Transfers to sales |

---

## 📞 Configuration

### Environment Variables

```env
# .env (Backend)
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
DATABASE_URL=postgresql://...
SCRAPER_TIMEOUT=60
SCRAPER_MAX_PAGES=20
```

### Twilio Webhook Setup

1. Go to Twilio Console → Phone Numbers → Your Number
2. Set Voice webhook: `POST https://yourserver.com/telephony/incoming/{tenant_id}`
3. Test with curl or Twilio CLI

---

## 🧪 Testing

```bash
# API test
curl -X POST http://localhost:8000/api/appointments/tenant-1/book \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_phone": "+15551234567",
    "scheduled_datetime": "2026-07-10T10:00:00"
  }'
```

---

## 🚀 Deployment

```bash
# Docker
docker build -t perfect-assistant .
docker run -p 8000:8000 --env-file .env perfect-assistant

# Vercel (Frontend)
vercel deploy
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

---

## 📖 Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) — Full setup & deployment guide
- [docs/FEATURE_SPEC.md](docs/FEATURE_SPEC.md) — Complete feature specification
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) — PostgreSQL schema
- [docs/WEB_SCRAPER_SPEC.md](docs/WEB_SCRAPER_SPEC.md) — Scraper details

---

## 🔒 Security

- Store API keys in environment variables
- Use HTTPS in production
- Implement JWT auth for API endpoints
- Verify Twilio webhook signatures
- Rate limit and monitor OpenAI usage

---

## 🤝 Contributing

Contributions welcome! Please fork, branch, commit, and submit a PR.

---

## 📄 License

[Your License]

---

**Status**: Phase 1-3 ✅ Complete | Phase 4 ⏳ In Progress  
**Version**: 2.0.0 (Perfect Assistant)  
**Last Updated**: July 3, 2026
- [ ] Add `/public/sounds/order-alert.mp3` chime file to frontend
- [ ] Set up Twilio webhook URL to point to `/telephony/incoming/{tenant_id}`
