# Perfect Assistant — Deployment & Setup Guide

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL (or SQLite for development)
- Twilio account with verified phone number
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Twilio, OpenAI, and database credentials

# Run backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Update API endpoints if not localhost

# Run development server
npm run dev
```

### Access Applications

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

---

## Environment Variables

### Backend (.env)

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.7

# Twilio Configuration
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
OWNER_PHONE=+1...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/perfect_assistant
DATABASE_ECHO=false

# Web Scraper
SCRAPER_TIMEOUT=60
SCRAPER_MAX_PAGES=20

# Logging
LOG_LEVEL=INFO

# Deployment
ENVIRONMENT=development  # or production
PORT=8000
HOST=0.0.0.0
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## API Endpoints Summary

### 🏢 Business Management
```
POST /api/businesses/{tenant_id}/onboard
  - Input: {"website_url": "https://example.com"}
  - Scrapes website, builds AI context

GET /api/businesses/{tenant_id}/profile
  - Returns scraped business profile
```

### 📅 Appointments
```
GET /api/appointments/{tenant_id}/availability?date=2026-07-10&time=10:00
GET /api/appointments/{tenant_id}
GET /api/appointments/{tenant_id}/schedule/{date}
POST /api/appointments/{tenant_id}/book
DELETE /api/appointments/{tenant_id}/{appointment_id}
PATCH /api/appointments/{tenant_id}/{appointment_id}
```

### 📞 Leads & Payment Handoff
```
GET /api/leads/{tenant_id}
GET /api/leads/{tenant_id}/qualified?min_score=0.6
POST /api/leads/{tenant_id}
PATCH /api/leads/{tenant_id}/{lead_id}
```

### 📊 Actions (Orders, Appointments, Leads)
```
GET /api/actions/{tenant_id}?limit=50
```

### 🎧 Call Handling
```
POST /telephony/incoming/{tenant_id}
  - Webhook from Twilio for incoming calls

WS /telephony/ai-stream/{tenant_id}
  - WebSocket for real-time audio processing
```

### 📈 Dashboard
```
GET /dashboard/{tenant_id}/metrics
  - Daily metrics: calls, orders, leads

WS /api/kds/{tenant_id}/stream
  - Real-time action updates for admin dashboard
```

---

## Database Setup

### PostgreSQL

```bash
# Create database
createdb perfect_assistant

# Run migrations (using Alembic)
alembic upgrade head
```

###SQLite (Development Only)

```python
# Update .env
DATABASE_URL=sqlite:///./perfect_assistant.db
```

---

## Twilio Configuration

### Webhook Setup

1. Go to Twilio Console
2. Navigate to Phone Numbers → Your Numbers
3. Set **Webhooks**:
   - **Voice**: POST to `https://yourserver.com/telephony/incoming/{tenant_id}`
   - **Call Status Callbacks**: POST to `https://yourserver.com/telephony/callbacks`

### Example Twilio Setup

```python
# Send calls to your API
from twilio.rest import Client

client = Client(account_sid, auth_token)

call = client.calls.create(
    to="+15550001111",  # Customer
    from_="+15559990000",  # Your Twilio number
    url="https://yourserver.com/telephony/incoming/tenant_123"
)
```

---

## Deployment

### Docker

```dockerfile
# Dockerfile (backend)
FROM python:3.10

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build & run
docker build -t perfect-assistant .
docker run -p 8000:8000 --env-file .env perfect-assistant
```

### Cloud Deployment

#### Azure
```bash
az webapp up --name perfect-assistant --resource-group mygroup
```

#### AWS (Lambda + API Gateway)
```bash
# Use serverless framework
serverless deploy
```

#### Heroku
```bash
heroku create perfect-assistant
heroku config:set OPENAI_API_KEY=sk-...
git push heroku main
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### API Testing (with curl)

```bash
# Onboard a business
curl -X POST http://localhost:8000/api/businesses/tenant_123/onboard \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://i10education.com"}'

# Check appointment availability
curl http://localhost:8000/api/appointments/tenant_123/availability?date=2026-07-10&time=10:00

# Book appointment
curl -X POST http://localhost:8000/api/appointments/tenant_123/book \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_phone": "+15551234567",
    "customer_email": "john@example.com",
    "scheduled_datetime": "2026-07-10T10:00:00",
    "service_type": "Consultation",
    "duration_minutes": 30
  }'
```

---

## Monitoring & Logs

### View Logs

```bash
# Local development
tail -f server.log

# Docker
docker logs -f perfect-assistant-container

# Production
# Use CloudWatch (AWS), Monitor (Azure), or Stackdriver (GCP)
```

### Key Metrics to Monitor

- **Call Volume**: Incoming calls per day
- **AI Handling Rate**: % of calls handled without human transfer
- **Appointment Booking Rate**: Successful bookings per call
- **Lead Conversion**: Leads to payment
- **API Response Time**: Average latency
- **Error Rate**: 4xx/5xx errors

---

## Troubleshooting

### Twilio Not Receiving Calls
- Verify webhook URL is publicly accessible
- Check Twilio logs for callback errors
- Ensure phone number is active and verified

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -U user -h localhost -d perfect_assistant
```

### Web Scraper Not Extracting Data
- Check website robots.txt restrictions
- Verify URL is valid and accessible
- Try increasing SCRAPER_TIMEOUT

### AI Model Not Responding
- Verify OPENAI_API_KEY is valid
- Check OpenAI account quota/billing
- Review API usage and rate limits

---

## Next Steps

1. **Database**: Set up PostgreSQL and run migrations
2. **Twilio**: Configure webhooks and test call forwarding
3. **OpenAI**: Verify API key and model availability
4. **Frontend**: Build admin dashboard components
5. **Testing**: Write integration tests
6. **Deployment**: Choose cloud provider and deploy
7. **Monitoring**: Set up alerts and logging
8. **Scaling**: Consider load balancing for high volume

---

## Support

For issues or questions:
1. Check logs for error messages
2. Review Twilio & OpenAI documentation
3. Open issue on GitHub
4. Contact support team

---

**Version**: 2.0.0  
**Last Updated**: 2026-07-03
