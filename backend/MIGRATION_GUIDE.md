# Database Migration Guide

## Quick Start

### Option 1: Using Python (Recommended - Cross-platform)

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure database
cp .env.example .env
# Edit .env and set:
# DATABASE_URL=postgresql://user:password@localhost:5432/perfect_assistant
# or
# DATABASE_URL=sqlite:///./perfect_assistant.db

# 3. Initialize database tables
python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
"

# 4. Verify tables created
python -c "
from database import Base
from sqlalchemy import inspect
from sqlalchemy import create_engine
import os

db_url = os.getenv('DATABASE_URL', 'sqlite:///./perfect_assistant.db')
if 'sqlite' in db_url:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    print('Tables created:', inspector.get_table_names())
"
```

### Option 2: Manual SQL (PostgreSQL)

```bash
# 1. Connect to your PostgreSQL database
psql -U your_user -d perfect_assistant

# 2. Run the migration script
\i backend/migrations/001_initial_schema.sql

# 3. Verify tables
\dt
```

### Option 3: Manual SQL (SQLite)

```bash
# 1. Open SQLite
sqlite3 perfect_assistant.db

# 2. Run migration
.read backend/migrations/001_initial_schema_sqlite.sql

# 3. Verify tables
.tables
```

---

## Environment Configuration

### PostgreSQL (Production)

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/perfect_assistant
DATABASE_ECHO=false
```

### SQLite (Development)

```bash
# .env
DATABASE_URL=sqlite:///./perfect_assistant.db
DATABASE_ECHO=true
```

---

## Database Schema Overview

### Tables

| Table | Purpose | Records |
|-------|---------|---------|
| `businesses` | Tenant profiles & settings | 1 per business |
| `appointments` | Scheduled appointments | N per business |
| `actions` | Orders, leads, reservations | N per business |
| `conversations` | Call transcripts | N per business |
| `leads` | Sales leads | N per business |
| `orders` | Orders (KDS compat) | N per business |

### Multi-tenancy

All tables use `tenant_id` as the primary partition key. Data is completely isolated per tenant.

```sql
-- Example: Get all appointments for a tenant
SELECT * FROM appointments WHERE tenant_id = 'business_123';
```

---

## Alembic Setup (Advanced - Optional)

For automated migrations in production:

```bash
# Initialize Alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Check current version
alembic current

# Rollback
alembic downgrade -1
```

---

## Data Types Reference

### PostgreSQL
- `VARCHAR(n)` → String with max length
- `JSONB` → JSON with indexing support (preferred)
- `TIMESTAMP` → Date + Time
- `FLOAT` → Floating point number
- `INTEGER` → Integer number
- `TEXT` → Unlimited text
- `BOOLEAN` → True/False

### SQLite
- `TEXT` → String (any length)
- `TEXT` (JSON) → JSON as text (not typed)
- `TIMESTAMP` → Date + Time as text
- `REAL` → Floating point
- `INTEGER` → Integer
- `INTEGER` (boolean) → 0 = false, 1 = true

---

## Important Notes

⚠️ **Foreign Keys**
- All tables except `businesses` reference `tenant_id` with `ON DELETE CASCADE`
- Deleting a business deletes all related data

⚠️ **JSON Handling**
- PostgreSQL: Use JSONB (faster, indexable)
- SQLite: Use TEXT and parse in Python (use json.loads/dumps)

⚠️ **Indexing**
- Primary indexes on `tenant_id` for multi-tenant queries
- Secondary indexes on `status`, `created_at`, `action_type` for filtering
- Avoid over-indexing to reduce write performance

⚠️ **UTC Timestamps**
- All `created_at` and `updated_at` use UTC
- Frontend should convert to local timezone

---

## Troubleshooting

### "relation does not exist" error

```bash
# Check if tables exist
python -c "
from database import Base, engine
import asyncio

async def check():
    from sqlalchemy import inspect
    async with engine.begin() as conn:
        result = await conn.run_sync(lambda c: inspect(c).get_table_names())
        print('Tables:', result)

asyncio.run(check())
"
```

### Connection issues

```bash
# Test PostgreSQL connection
psql -U user -h localhost -d perfect_assistant -c "SELECT 1;"

# Test SQLite
python -c "import sqlite3; db = sqlite3.connect('perfect_assistant.db'); print(db.execute('SELECT 1').fetchone())"
```

### Wrong charset/encoding

```sql
-- PostgreSQL: Check encoding
SELECT datname, encoding FROM pg_database WHERE datname = 'perfect_assistant';

-- Should return: utf8 or UTF8
```

---

## Next Steps

1. ✅ Tables created and indexed
2. ⏳ Run backend with: `uvicorn main:app --reload`
3. ⏳ Test with: `curl http://localhost:8000/docs`
4. ⏳ Update backend modules to use SQLAlchemy ORM
5. ⏳ Write integration tests

---

**Migration Status**: Ready for Phase 4 Integration  
**Last Updated**: July 3, 2026
