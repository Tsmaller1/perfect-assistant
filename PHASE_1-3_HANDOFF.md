# Perfect Assistant — Phase 1-3 Handoff Brief

## 🎯 Executive Summary
Build the foundational infrastructure for Perfect Assistant: a generic AI receptionist platform that handles phone calls for ANY business type. Businesses submit their website → AI scrapes it → AI learns their business → AI answers calls, books appointments, qualifies leads → human handoff for payment.

---

## 📍 Current State
- ✅ Git repo: https://github.com/Tsmaller1/perfect-assistant.git
- ✅ Stack: Python FastAPI (backend) + Next.js (frontend) + Twilio
- ✅ Multi-tenant capable
- ✅ Basic KDS (kitchen display system) for orders
- ✅ WebSocket real-time streaming

**Workspace:** `c:\Users\lalai\OneDrive\Downloads\Perfect Assistant\pine-sales-ai`

---

## 🚀 Phase 1: Foundation & Planning

### 1.1 Feature Specification Document
**Deliverable:** `docs/FEATURE_SPEC.md`

Document these capabilities:
- **Business Onboarding**: Website URL → Auto-scrape → AI learns business
- **Incoming Call Flow**: Customer calls → AI answers with business context
- **AI Capabilities**:
  - Answer questions about business offerings
  - Schedule appointments/reservations
  - Take orders (generic, not just food)
  - Handle payment qualifications
  - Transfer to human rep
- **Human Handoff**: When customer ready to pay or requests live person
- **Admin Dashboard**: View calls, leads, appointments, manage AI behavior
- **Multi-tenant**: Each business is isolated tenant

### 1.2 Database Schema
**Deliverable:** `docs/DATABASE_SCHEMA.md` or `backend/models/schema.sql`

Design tables for:
- **Businesses**: tenant_id, business_name, website_url, scraped_data (JSON), phone_number, hours, etc.
- **Conversations**: call_id, tenant_id, transcript, ai_response, timestamp
- **Appointments**: appointment_id, tenant_id, customer_info, datetime, status
- **Leads**: lead_id, tenant_id, customer_contact, qualification_status, callback_needed
- **Orders**: order_id, tenant_id, items, customer_info, status
- **Call History**: call_id, tenant_id, duration, transcription, ai_handled, transferred_to_human

### 1.3 Web Scraper Requirements
**Deliverable:** `docs/WEB_SCRAPER_SPEC.md`

Specify what to extract from websites:
- Business info (name, address, hours, phone)
- Menu/Services/Products description
- Pricing information
- FAQ/Common questions
- Images/logos
- Contact methods
- Appointment booking links (if any)
- Terms/Policies

---

## 🔧 Phase 2: Core Infrastructure

### 2.1 Build Web Scraper Module
**Deliverable:** `backend/scraper.py` (enhance existing)

Requirements:
- Extract structured business data from URL
- Handle different website structures (use BeautifulSoup + Selenium if needed)
- Store scraped data in database
- Return: business_profile JSON
- Dependencies to add: `beautifulsoup4`, `selenium` (or `playwright`), `langchain` for parsing

**Function signature:**
```python
async def scrape_business_website(url: str, tenant_id: str) -> dict:
    """
    Returns:
    {
        "business_name": "...",
        "address": "...",
        "hours": {...},
        "phone": "...",
        "services": [...],
        "menu": {...},
        "pricing": {...},
        "ai_context": "Full knowledge base for AI"
    }
    """
```

### 2.2 Create Business Onboarding API
**Deliverable:** New endpoint in `backend/telephony_router.py`

```python
@router.post("/businesses/{tenant_id}/onboard")
async def onboard_business(tenant_id: str, body: dict):
    # body = {"website_url": "i10education.com"}
    # 1. Scrape website
    # 2. Store in database
    # 3. Build AI context
    # Return: onboarding_status
```

### 2.3 Generalize the Action Queue System
**Deliverable:** `backend/action_queue.py` (rename/refactor from `kds_manager.py`)

Change from restaurant-only to generic:
- Rename `KDS` → `ActionQueue`
- Support action types: `order`, `appointment`, `lead`, `task`
- Each action has metadata: `action_type`, `priority`, `tenant_id`, `customer_info`
- WebSocket broadcasts to appropriate display screens

**Function signatures:**
```python
async def broadcast_new_action(tenant_id: str, action: dict):
    # action = {
    #   "type": "appointment|order|lead",
    #   "data": {...}
    # }
```

### 2.4 Update Environment Config
**Deliverable:** Enhanced `backend/.env.example`

Add:
```env
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
OWNER_PHONE=+1...
DATABASE_URL=postgresql://...
SCRAPER_TIMEOUT=30
AI_MODEL=gpt-4
```

---

## 🎨 Phase 3: Features

### 3.1 Appointment/Reservation System
**Deliverable:** `backend/appointments.py`

- Calendar availability management
- Booking endpoint
- Conflict detection
- Confirmation logic
- Cancellation flow

**Functions:**
```python
async def check_availability(tenant_id: str, datetime: str) -> bool:
    pass

async def create_appointment(tenant_id: str, appointment: dict) -> dict:
    pass

async def get_appointments(tenant_id: str) -> list:
    pass
```

### 3.2 Business Admin Dashboard
**Deliverable:** `frontend/app/admin/[tenantId]/page.js` + components

Screens needed:
- **Dashboard**: Overview of calls, appointments, leads (today)
- **Call History**: Recordings, transcripts, AI handling stats
- **Appointments**: Calendar view, manage bookings
- **Leads**: View qualified leads, callback needed
- **AI Settings**: Train AI behavior, manage business context
- **Analytics**: Charts on call volume, conversion rates

### 3.3 Payment Handoff System
**Deliverable:** `backend/payment_handoff.py`

Logic:
- Detect when customer ready to pay (from AI conversation)
- Trigger human transfer via Twilio
- Log lead with customer contact info
- Mark for sales rep action

**Function:**
```python
async def initiate_payment_handoff(tenant_id: str, call_sid: str, customer_info: dict):
    # Transfer call to human
    # Create lead record
    # Notify admin dashboard
    pass
```

### 3.4 Conversation Memory & Context
**Deliverable:** `backend/conversation_memory.py`

- Store conversation transcripts
- Reference business scraped data during calls
- Build context window for AI prompts
- Track conversation state (question asked, answer given, next step)

---

## 📋 Deliverables Checklist

### Phase 1 Outputs:
- [ ] `docs/FEATURE_SPEC.md` (2-3 pages)
- [ ] `docs/DATABASE_SCHEMA.md` (with SQL or model definitions)
- [ ] `docs/WEB_SCRAPER_SPEC.md` (what to extract)

### Phase 2 Outputs:
- [ ] Enhanced `backend/scraper.py` with web scraping logic
- [ ] New endpoint: `POST /businesses/{tenant_id}/onboard`
- [ ] `backend/action_queue.py` (generalized from KDS)
- [ ] Updated `backend/.env.example` with new variables

### Phase 3 Outputs:
- [ ] `backend/appointments.py` with 3-4 core functions
- [ ] Admin dashboard UI: `/admin/[tenantId]/` (React components)
- [ ] `backend/payment_handoff.py` with transfer logic
- [ ] `backend/conversation_memory.py` for context storage

---

## 🔗 Integration Points

After Phase 3 completes, the original agent will:
1. Integrate new modules into main FastAPI app
2. Update Twilio call handler to use business context
3. Build agent prompt template using business data
4. Deploy & test end-to-end
5. Create deployment pipeline

---

## 📚 Reference Files

Current structure to keep in mind:
- Backend main: `backend/main.py`
- Telephony router: `backend/telephony_router.py`
- Agent engine: `backend/agent_engine.py`
- Frontend dashboard: `frontend/components/Dashboard.jsx`

---

## ⚙️ Technology Stack

**Backend:**
- FastAPI
- Python 3.9+
- Twilio SDK
- OpenAI API
- Database: PostgreSQL (recommended) or SQLite for MVP
- Web scraping: BeautifulSoup, Selenium/Playwright

**Frontend:**
- Next.js (already set up)
- React
- Tailwind CSS (already set up)

---

## 🎯 Success Criteria

Phase 1-3 complete when:
1. ✅ All 3 phases have documentation + code artifacts
2. ✅ Web scraper can extract and store business data
3. ✅ API endpoints for onboarding + appointments + handoff working
4. ✅ Admin dashboard displays calls, appointments, leads
5. ✅ Database schema matches feature requirements
6. ✅ All new env vars documented

---

**Once complete:** Push to `main` branch with commit message: `"Phase 1-3: Core infrastructure for Perfect Assistant"`

Then original agent will take Phase 4 (integration, testing, deployment).
