# Perfect Assistant — Feature Specification

## Overview
Perfect Assistant is a generic AI receptionist platform that enables businesses to accept calls, answer questions, book appointments, take orders, and qualify leads. The AI learns business context by scraping the company's website and uses that knowledge to provide accurate, business-specific responses.

---

## Core Features

### 1. Business Onboarding
- **Input**: Business website URL (e.g., i10education.com)
- **Process**:
  - Scrape website for business info, hours, services, pricing
  - Extract text, structure, and context
  - Build AI knowledge base
  - Store scraped data in database
- **Output**: Business profile ready for AI interactions

**Endpoints:**
- `POST /api/businesses/{tenant_id}/onboard` — Submit website URL
- `GET /api/businesses/{tenant_id}/profile` — Retrieve scraped profile

---

### 2. Incoming Call Handling
**Flow:**
1. Customer dials business's Twilio phone number
2. Request hits `/telephony/incoming/{tenant_id}`
3. AI answers with business context ("Thanks for calling I10 Education!")
4. AI processes customer audio in real-time via WebSocket
5. AI responds with contextually accurate answers

**Capabilities:**
- Answer FAQs about business
- Explain products/services
- Schedule appointments/reservations
- Take orders (generic)
- Qualify leads for sales team
- Transfer to human for payment

---

### 3. Appointment/Reservation System
- **Check Availability**: `GET /api/appointments/{tenant_id}/availability?date=2026-07-10`
- **Book Appointment**: `POST /api/appointments/{tenant_id}/book`
- **List Appointments**: `GET /api/appointments/{tenant_id}`
- **Cancel Appointment**: `DELETE /api/appointments/{tenant_id}/{appointment_id}`

**Data stored:**
- Customer name, email, phone
- Desired date/time
- Service type
- Status (booked, confirmed, completed, cancelled)

---

### 4. Action Queue (Generalized from KDS)
Replaces restaurant-specific KDS with multi-purpose action queue.

**Action Types:**
- `ORDER` — Food/product orders
- `APPOINTMENT` — Scheduled appointments
- `LEAD` — Customer qualified for sales
- `RESERVATION` — Table/resource reservation

**Real-time Updates:**
- WebSocket broadcasts to business admin dashboards
- Each action appears on appropriate display
- Status updates: `NEW` → `IN_PROGRESS` → `COMPLETED`

---

### 5. Payment Handoff System
**Trigger:** When AI detects customer ready to pay:
- AI says: "Let me transfer you to our team to process payment"
- Call transfers to human rep (via Twilio)
- Lead record created with customer contact info
- Admin dashboard notified

**Endpoints:**
- `POST /api/payment-handoff/{tenant_id}/transfer` — Initiate transfer
- `POST /api/leads/{tenant_id}` — Create lead record
- `GET /api/leads/{tenant_id}` — List leads

---

### 6. Admin Dashboard
**Business Owner Views:**
- **Overview**: Today's calls, appointments, orders, leads
- **Call History**: 
  - Transcripts
  - AI handling success rate
  - Duration
  - Recordings (future)
- **Appointments Calendar**: 
  - Availability
  - Confirmed bookings
  - Cancellations
- **Leads/Sales Queue**:
  - Qualified leads
  - Contact info
  - Call notes
  - Status (pending, contacted, converted)
- **Orders**: 
  - New orders display
  - Status tracking
  - Customer info
- **AI Settings**: 
  - Manage business context
  - Update hours/services
  - Train AI behavior

---

### 7. Conversation Memory & Context
**Stores:**
- Full conversation transcripts
- Customer info extracted during call
- Intent detected (book appointment, ask question, place order)
- AI responses generated
- Outcomes (order placed, appointment booked, transferred to human)

**Used for:**
- Building rich context for AI prompts
- Analytics
- Audit trails
- Follow-up workflows

---

## Data Models

### Business
```
- tenant_id (UUID)
- business_name (string)
- website_url (string)
- phone_number (string)
- address (string)
- hours (JSON — day → hours map)
- scraped_data (JSON — full business context)
- ai_context (text — formatted for AI system prompt)
- created_at (timestamp)
- updated_at (timestamp)
```

### Appointment
```
- appointment_id (UUID)
- tenant_id (UUID)
- customer_name (string)
- customer_email (string)
- customer_phone (string)
- scheduled_datetime (timestamp)
- service_type (string)
- duration_minutes (integer)
- status (BOOKED, CONFIRMED, COMPLETED, CANCELLED)
- notes (string)
- created_at (timestamp)
- updated_at (timestamp)
```

### Action (Orders, Leads, Appointments)
```
- action_id (UUID)
- tenant_id (UUID)
- action_type (ORDER, APPOINTMENT, LEAD, RESERVATION)
- customer_info (JSON)
- action_data (JSON — flexible structure)
- status (NEW, IN_PROGRESS, COMPLETED, FAILED)
- created_at (timestamp)
- updated_at (timestamp)
```

### Conversation
```
- conversation_id (UUID)
- tenant_id (UUID)
- call_sid (string — Twilio call ID)
- customer_phone (string)
- transcript (text)
- intent (string)
- entities (JSON — extracted data)
- ai_handled (boolean)
- transferred_to_human (boolean)
- outcome (string)
- created_at (timestamp)
```

### Lead
```
- lead_id (UUID)
- tenant_id (UUID)
- customer_name (string)
- customer_phone (string)
- customer_email (string)
- qualification_score (float 0-1)
- notes (text)
- status (NEW, CONTACTED, CONVERTED, LOST)
- created_at (timestamp)
- updated_at (timestamp)
```

---

## API Endpoints Summary

### Business Management
- `POST /api/businesses/{tenant_id}/onboard` — Onboard new business
- `GET /api/businesses/{tenant_id}/profile` — Get business profile

### Appointments
- `GET /api/appointments/{tenant_id}/availability` — Check availability
- `POST /api/appointments/{tenant_id}/book` — Book appointment
- `GET /api/appointments/{tenant_id}` — List all appointments
- `DELETE /api/appointments/{tenant_id}/{appointment_id}` — Cancel

### Leads
- `GET /api/leads/{tenant_id}` — List leads
- `POST /api/leads/{tenant_id}` — Create lead
- `PATCH /api/leads/{tenant_id}/{lead_id}` — Update lead status

### Action Queue
- `GET /api/actions/{tenant_id}` — Get current actions
- `PATCH /api/actions/{tenant_id}/{action_id}` — Update action status

### Call Handling
- `POST /telephony/incoming/{tenant_id}` — Handle incoming call (Twilio webhook)
- `POST /telephony/toggle-mode/{tenant_id}` — Switch AI ↔ human

### Payment Handoff
- `POST /api/payment-handoff/{tenant_id}/transfer` — Initiate transfer
- `GET /api/payment-handoff/{tenant_id}/status/{call_sid}` — Check transfer status

### WebSocket Streams
- `WS /api/kds/{tenant_id}/stream` — Real-time action updates (admin)
- `WS /telephony/ai-stream/{tenant_id}` — Real-time call audio/response

---

## Success Criteria
✅ Business can onboard via URL  
✅ AI answers calls with business context  
✅ Customers can book appointments via phone  
✅ Orders/actions broadcast to admin dashboard  
✅ Leads generated and tracked  
✅ Payment handoff to human works  
✅ All conversations stored with full context  
