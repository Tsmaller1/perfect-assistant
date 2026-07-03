# Supabase Setup Guide — Perfect Assistant

## ✅ Your Supabase Project Connected

**Project:** taaakkckfumdqqlvvnie  
**URL:** https://taaakkckfumdqqlvvnie.supabase.co  
**Database:** postgres  

---

## 🚀 Quick Start

### 1. Copy Environment Variables

```bash
cd backend
cp .env.example .env
```

The `.env` file now includes:
```env
DATABASE_URL=postgresql://postgres:Adonis085!!!1@taaakkckfumdqqlvvnie.supabase.co:5432/postgres
SUPABASE_URL=https://taaakkckfumdqqlvvnie.supabase.co
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `asyncpg` (PostgreSQL async driver)
- `sqlalchemy` (ORM)
- All other dependencies

### 3. Initialize Database

```bash
python setup_supabase.py
```

This will:
- ✅ Test Supabase connection
- ✅ Create all 6 tables
- ✅ Verify tables created
- ✅ Show row counts

**Expected output:**
```
✅ Connected to Supabase PostgreSQL
✅ Tables created successfully
✅ Found 6 tables:
   ✓ businesses
   ✓ appointments
   ✓ actions
   ✓ conversations
   ✓ leads
   ✓ orders
```

### 4. Start Backend

```bash
uvicorn main:app --reload
```

Visit:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

## 📊 Access Supabase Dashboard

1. Go to: https://app.supabase.com
2. Project: **taaakkckfumdqqlvvnie**
3. Database → SQL Editor
4. Run queries directly from the web UI

---

## 🔐 Security Notes

### Production Checklist

- ⚠️ **Password in .env** — Never commit `.env` to git!
  ```bash
  # Add to .gitignore
  echo ".env" >> .gitignore
  ```

- ⚠️ **Connection String** — Keep DATABASE_URL secret
  - Don't share in logs
  - Use environment variables in production
  - Rotate password regularly via Supabase dashboard

- ⚠️ **Row Level Security (RLS)** — Disabled by default
  - Enable RLS policies in production
  - Restrict queries by tenant_id

### Enable RLS (Optional - Production)

```sql
-- In Supabase SQL Editor

-- Enable RLS
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own tenant data
CREATE POLICY "Tenant isolation" ON businesses
  FOR SELECT USING (
    auth.jwt() ->> 'tenant_id' = tenant_id
  );
```

---

## 🛠️ Common Tasks

### View All Tables

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

### Check Table Structure

```sql
\d businesses

-- Or in SQL Editor:
SELECT * FROM information_schema.columns 
WHERE table_name = 'businesses';
```

### Insert Test Business

```sql
INSERT INTO businesses (
    tenant_id,
    business_name,
    phone,
    owner_phone
) VALUES (
    'test_tenant_001',
    'Test Business',
    '+1-555-123-4567',
    '+1-555-999-0000'
);
```

### Query by Tenant

```sql
-- Get all appointments for a tenant
SELECT * FROM appointments 
WHERE tenant_id = 'test_tenant_001';
```

### Export Data

```bash
# Export all data
pg_dump "postgresql://postgres:Adonis085!!!1@taaakkckfumdqqlvvnie.supabase.co:5432/postgres" > backup.sql

# Import data
psql "postgresql://postgres:Adonis085!!!1@taaakkckfumdqqlvvnie.supabase.co:5432/postgres" < backup.sql
```

---

## 🔗 Connection Details

| Setting | Value |
|---------|-------|
| **Host** | taaakkckfumdqqlvvnie.supabase.co |
| **Port** | 5432 |
| **Database** | postgres |
| **User** | postgres |
| **Password** | Adonis085!!!1 |
| **SSL** | Required |

### Connection String Formats

**SQLAlchemy (Python):**
```python
DATABASE_URL = "postgresql+asyncpg://postgres:Adonis085!!!1@taaakkckfumdqqlvvnie.supabase.co:5432/postgres"
```

**psql (CLI):**
```bash
psql -h taaakkckfumdqqlvvnie.supabase.co -U postgres -d postgres
```

**Node.js:**
```javascript
const { createClient } = require('@supabase/supabase-js')
const supabase = createClient(
  'https://taaakkckfumdqqlvvnie.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
)
```

---

## ⚠️ Troubleshooting

### Connection Refused

```
Error: could not connect to server: Connection refused
```

**Solution:**
- Check DATABASE_URL in .env
- Verify Supabase project is active
- Check firewall/network

### SSL Certificate Error

```
Error: CERTIFICATE_VERIFY_FAILED
```

**Solution:** Supabase requires SSL. This is already configured in `database.py`.

### Table Not Found

```
Error: relation "businesses" does not exist
```

**Solution:**
```bash
# Re-run setup
python setup_supabase.py

# Or check tables exist
psql -c "\dt"
```

### Permission Denied

```
Error: permission denied for schema public
```

**Solution:**
- Use default `postgres` user (already configured)
- Or create new role with permissions in Supabase dashboard

---

## 📈 Monitoring

### Check Database Size

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Connection Count

```sql
SELECT count(*) as connection_count FROM pg_stat_activity;
```

### View Recent Queries (Supabase Dashboard)

- Go to: **Monitoring** → **Logs**
- Filter: Database Logs
- View slow queries and errors

---

## 🚀 Next Steps

1. ✅ Database connected to Supabase
2. ⏳ Migrate backend modules to use SQLAlchemy ORM
3. ⏳ Update API endpoints to use database
4. ⏳ Write integration tests
5. ⏳ Deploy backend to cloud (Railway, Fly.io, etc)

---

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

**Status**: Supabase Connected ✅  
**Last Updated**: July 3, 2026  
**Version**: 2.0.0 (Perfect Assistant)
