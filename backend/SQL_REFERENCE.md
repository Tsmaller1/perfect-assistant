# Perfect Assistant — SQL Code Reference

Complete SQL guide for database operations. Use these queries to manage Perfect Assistant data.

---

## Table of Contents

1. [Setup & Initialization](#setup--initialization)
2. [Businesses (Tenants)](#businesses-tenants)
3. [Appointments](#appointments)
4. [Actions](#actions)
5. [Conversations](#conversations)
6. [Leads](#leads)
7. [Orders](#orders)
8. [Maintenance & Analytics](#maintenance--analytics)
9. [Multi-tenancy Queries](#multi-tenancy-queries)

---

## Setup & Initialization

### Create All Tables (PostgreSQL)

```sql
-- Run this file
\i backend/migrations/001_initial_schema.sql
```

### Create All Tables (SQLite)

```sql
-- Run this file
.read backend/migrations/001_initial_schema_sqlite.sql
```

### Drop All Tables (DANGER - Development Only)

```sql
-- PostgreSQL
DROP TABLE IF EXISTS business_daily_summary CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS actions CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS businesses CASCADE;

-- SQLite
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS actions;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS businesses;
```

---

## Businesses (Tenants)

### Create a New Business

```sql
INSERT INTO businesses (
    tenant_id,
    business_name,
    website_url,
    phone,
    email,
    address,
    owner_phone,
    ai_context
) VALUES (
    'i10education_001',
    'I10 Education',
    'https://i10education.com',
    '+1-555-123-4567',
    'info@i10education.com',
    '123 Education Ave, San Francisco, CA',
    '+1-555-999-0000',
    'I10 Education offers online coding courses for beginners...'
);
```

### Update Business Profile

```sql
UPDATE businesses
SET
    business_name = 'I10 Education Services',
    services = '[{"name": "Python Course", "price": 99.99}, {"name": "JavaScript Course", "price": 89.99}]',
    hours_of_operation = '{"monday": "9-5", "tuesday": "9-5", "wednesday": "9-5", "thursday": "9-5", "friday": "9-5", "saturday": "10-4", "sunday": "closed"}',
    updated_at = CURRENT_TIMESTAMP
WHERE tenant_id = 'i10education_001';
```

### Get Business Details

```sql
SELECT * FROM businesses WHERE tenant_id = 'i10education_001';
```

### Get All Businesses

```sql
SELECT tenant_id, business_name, phone, email, created_at
FROM businesses
ORDER BY created_at DESC;
```

### Delete a Business (Cascades to all related data)

```sql
DELETE FROM businesses WHERE tenant_id = 'i10education_001';
```

---

## Appointments

### Book an Appointment

```sql
INSERT INTO appointments (
    appointment_id,
    tenant_id,
    customer_name,
    customer_email,
    customer_phone,
    scheduled_datetime,
    service_type,
    duration_minutes,
    status,
    notes
) VALUES (
    'appt_20260704_001',
    'i10education_001',
    'John Doe',
    'john@example.com',
    '+1-555-111-2222',
    '2026-07-04 14:00:00',
    'Course Consultation',
    30,
    'BOOKED',
    'First-time customer, interested in Python'
);
```

### Check Availability (No Overlapping)

```sql
SELECT 
    scheduled_datetime,
    duration_minutes,
    customer_name,
    status
FROM appointments
WHERE 
    tenant_id = 'i10education_001'
    AND scheduled_datetime BETWEEN '2026-07-04 14:00' AND '2026-07-04 15:00'
    AND status != 'CANCELLED';

-- If no results → slot is available
```

### Get Daily Schedule

```sql
SELECT 
    appointment_id,
    scheduled_datetime,
    duration_minutes,
    customer_name,
    customer_phone,
    service_type,
    status
FROM appointments
WHERE 
    tenant_id = 'i10education_001'
    AND DATE(scheduled_datetime) = '2026-07-04'
ORDER BY scheduled_datetime ASC;
```

### Confirm Appointment

```sql
UPDATE appointments
SET status = 'CONFIRMED', updated_at = CURRENT_TIMESTAMP
WHERE appointment_id = 'appt_20260704_001';
```

### Cancel Appointment

```sql
UPDATE appointments
SET 
    status = 'CANCELLED',
    notes = COALESCE(notes, '') || ' | Cancelled: Customer requested',
    updated_at = CURRENT_TIMESTAMP
WHERE appointment_id = 'appt_20260704_001';
```

### Get Upcoming Appointments (Next 7 Days)

```sql
SELECT 
    appointment_id,
    customer_name,
    customer_phone,
    scheduled_datetime,
    service_type,
    status
FROM appointments
WHERE 
    tenant_id = 'i10education_001'
    AND scheduled_datetime BETWEEN NOW() AND NOW() + INTERVAL '7 days'
    AND status IN ('BOOKED', 'CONFIRMED')
ORDER BY scheduled_datetime ASC;
```

---

## Actions

### Create an Action

```sql
-- ORDER
INSERT INTO actions (
    action_id,
    tenant_id,
    action_type,
    customer_info,
    action_data,
    status,
    notes
) VALUES (
    'act_20260703_001',
    'i10education_001',
    'ORDER',
    '{"name": "Alice Smith", "phone": "+1-555-222-3333", "email": "alice@example.com"}',
    '{"items": [{"name": "Python Course", "quantity": 1, "price": 99.99}], "total": 99.99}',
    'NEW',
    'Online course purchase'
);

-- LEAD
INSERT INTO actions (
    action_id,
    tenant_id,
    action_type,
    customer_info,
    action_data,
    status
) VALUES (
    'act_20260703_002',
    'i10education_001',
    'LEAD',
    '{"name": "Bob Johnson", "phone": "+1-555-333-4444"}',
    '{"interest": "Corporate Training", "budget": "5000-10000"}',
    'NEW'
);
```

### Update Action Status

```sql
UPDATE actions
SET 
    status = 'COMPLETED',
    notes = COALESCE(notes, '') || ' | Completed at fulfillment',
    updated_at = CURRENT_TIMESTAMP
WHERE action_id = 'act_20260703_001';
```

### Get Recent Actions

```sql
SELECT 
    action_id,
    action_type,
    customer_info ->> 'name' AS customer_name,
    status,
    created_at
FROM actions
WHERE 
    tenant_id = 'i10education_001'
ORDER BY created_at DESC
LIMIT 50;
```

### Get Actions by Type

```sql
SELECT 
    action_id,
    action_type,
    status,
    created_at
FROM actions
WHERE 
    tenant_id = 'i10education_001'
    AND action_type = 'ORDER'
ORDER BY created_at DESC;
```

---

## Conversations

### Create a Conversation

```sql
INSERT INTO conversations (
    conversation_id,
    tenant_id,
    call_sid,
    customer_phone,
    transcript,
    entities,
    intent,
    outcome
) VALUES (
    'conv_20260703_001',
    'i10education_001',
    'CA1234567890abcdef',
    '+1-555-444-5555',
    '[
        {"role": "ai", "text": "Thank you for calling I10 Education", "timestamp": "2026-07-03T10:00:00Z"},
        {"role": "user", "text": "Hi, I want to learn Python", "timestamp": "2026-07-03T10:00:05Z"},
        {"role": "ai", "text": "Great! We have a Python course", "timestamp": "2026-07-03T10:00:10Z"}
    ]',
    '{"name": "Customer", "phone": "+1-555-444-5555", "intent": "COURSE_INQUIRY"}',
    'BOOK_APPOINTMENT',
    'COMPLETED'
);
```

### Get Conversation Details

```sql
SELECT 
    conversation_id,
    customer_phone,
    intent,
    outcome,
    transcript,
    entities,
    created_at
FROM conversations
WHERE conversation_id = 'conv_20260703_001';
```

### Get Recent Conversations

```sql
SELECT 
    conversation_id,
    customer_phone,
    intent,
    outcome,
    duration_seconds,
    created_at
FROM conversations
WHERE 
    tenant_id = 'i10education_001'
ORDER BY created_at DESC
LIMIT 100;
```

### Get Conversations by Outcome

```sql
SELECT 
    conversation_id,
    customer_phone,
    intent,
    outcome,
    transferred_to_human,
    created_at
FROM conversations
WHERE 
    tenant_id = 'i10education_001'
    AND outcome = 'COMPLETED'
ORDER BY created_at DESC;
```

---

## Leads

### Create a Lead (From Payment Handoff)

```sql
INSERT INTO leads (
    lead_id,
    tenant_id,
    call_sid,
    customer_name,
    customer_phone,
    customer_email,
    order_value,
    order_items,
    status,
    qualification_score,
    notes
) VALUES (
    'lead_20260703_001',
    'i10education_001',
    'CA1234567890abcdef',
    'Carol Williams',
    '+1-555-666-7777',
    'carol@example.com',
    250.00,
    '[{"name": "Corporate Training Package", "quantity": 1, "price": 250.00}]',
    'PENDING',
    0.85,
    'High-value corporate client, budget confirmed'
);
```

### Get All Leads

```sql
SELECT 
    lead_id,
    customer_name,
    customer_phone,
    order_value,
    status,
    qualification_score,
    created_at
FROM leads
WHERE tenant_id = 'i10education_001'
ORDER BY created_at DESC;
```

### Get Qualified Leads (Score > 0.6)

```sql
SELECT 
    lead_id,
    customer_name,
    customer_phone,
    customer_email,
    order_value,
    qualification_score,
    status
FROM leads
WHERE 
    tenant_id = 'i10education_001'
    AND qualification_score >= 0.6
    AND status IN ('PENDING', 'AUTHORIZED')
ORDER BY qualification_score DESC;
```

### Update Lead Status

```sql
UPDATE leads
SET 
    status = 'CONVERTED',
    payment_status = 'COMPLETED',
    notes = 'Converted to customer',
    updated_at = CURRENT_TIMESTAMP
WHERE lead_id = 'lead_20260703_001';
```

---

## Orders

### Create an Order

```sql
INSERT INTO orders (
    order_id,
    tenant_id,
    customer_name,
    customer_phone,
    items,
    status,
    total_price,
    notes
) VALUES (
    'ord_20260703_001',
    'i10education_001',
    'David Brown',
    '+1-555-888-9999',
    '[
        {"name": "Python Course", "quantity": 1, "special_instructions": "Add certificate"},
        {"name": "Mentoring Package", "quantity": 1, "special_instructions": "1-on-1 sessions"}
    ]',
    'NEW',
    299.99,
    'Premium student enrollment'
);
```

### Get All Orders

```sql
SELECT 
    order_id,
    customer_name,
    customer_phone,
    status,
    total_price,
    created_at
FROM orders
WHERE tenant_id = 'i10education_001'
ORDER BY created_at DESC;
```

### Update Order Status

```sql
UPDATE orders
SET 
    status = 'READY',
    updated_at = CURRENT_TIMESTAMP
WHERE order_id = 'ord_20260703_001';
```

---

## Maintenance & Analytics

### Count Records by Type

```sql
SELECT 
    'Appointments' AS type,
    COUNT(*) AS count
FROM appointments
WHERE tenant_id = 'i10education_001'
UNION ALL
SELECT 'Actions', COUNT(*) FROM actions WHERE tenant_id = 'i10education_001'
UNION ALL
SELECT 'Conversations', COUNT(*) FROM conversations WHERE tenant_id = 'i10education_001'
UNION ALL
SELECT 'Leads', COUNT(*) FROM leads WHERE tenant_id = 'i10education_001'
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders WHERE tenant_id = 'i10education_001';
```

### Daily Summary

```sql
SELECT 
    DATE(created_at) AS date,
    COUNT(DISTINCT 
        CASE WHEN 'appointments' = 'appointments' THEN appointment_id END
    ) AS appointments,
    COUNT(DISTINCT 
        CASE WHEN 'actions' = 'actions' THEN action_id END
    ) AS actions,
    COUNT(DISTINCT 
        CASE WHEN 'conversations' = 'conversations' THEN conversation_id END
    ) AS conversations,
    COUNT(DISTINCT 
        CASE WHEN 'leads' = 'leads' THEN lead_id END
    ) AS leads
FROM (
    SELECT created_at, appointment_id, NULL, NULL, NULL FROM appointments WHERE tenant_id = 'i10education_001'
    UNION ALL
    SELECT created_at, NULL, action_id, NULL, NULL FROM actions WHERE tenant_id = 'i10education_001'
    UNION ALL
    SELECT created_at, NULL, NULL, conversation_id, NULL FROM conversations WHERE tenant_id = 'i10education_001'
    UNION ALL
    SELECT created_at, NULL, NULL, NULL, lead_id FROM leads WHERE tenant_id = 'i10education_001'
) combined
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Total Revenue (Orders)

```sql
SELECT 
    SUM(total_price) AS total_revenue,
    COUNT(*) AS order_count,
    AVG(total_price) AS avg_order_value
FROM orders
WHERE 
    tenant_id = 'i10education_001'
    AND status != 'CANCELLED';
```

### Table Size (PostgreSQL)

```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Backup (PostgreSQL)

```bash
pg_dump -U user -d perfect_assistant > backup.sql
```

### Restore (PostgreSQL)

```bash
psql -U user -d perfect_assistant < backup.sql
```

---

## Multi-tenancy Queries

### Get Data for Multiple Tenants

```sql
-- Count by tenant
SELECT 
    tenant_id,
    COUNT(DISTINCT appointment_id) AS appointments,
    COUNT(DISTINCT action_id) AS actions,
    COUNT(DISTINCT conversation_id) AS conversations
FROM (
    SELECT tenant_id, appointment_id, NULL::VARCHAR, NULL::VARCHAR FROM appointments
    UNION ALL
    SELECT tenant_id, NULL, action_id, NULL FROM actions
    UNION ALL
    SELECT tenant_id, NULL, NULL, conversation_id FROM conversations
) combined
GROUP BY tenant_id
ORDER BY tenant_id;
```

### Query Isolation Pattern

```sql
-- Always filter by tenant_id for security
SELECT * FROM appointments
WHERE tenant_id = 'i10education_001'  -- REQUIRED
AND status = 'BOOKED';
```

---

## Performance Tips

✅ **Always filter by tenant_id first**
```sql
-- GOOD
SELECT * FROM actions WHERE tenant_id = 'tenant_1' AND status = 'NEW';

-- SLOW
SELECT * FROM actions WHERE status = 'NEW' AND tenant_id = 'tenant_1';
```

✅ **Use indexed columns for WHERE clauses**
- `tenant_id` (primary)
- `status`, `action_type`, `created_at` (secondary)

✅ **Limit large result sets**
```sql
SELECT * FROM conversations WHERE tenant_id = 'i10education_001' LIMIT 100;
```

❌ **Avoid full table scans**
```sql
-- BAD - no index on customer_name
SELECT * FROM appointments WHERE customer_name LIKE 'John%';

-- BETTER - use indexed column
SELECT * FROM appointments WHERE tenant_id = 'tenant_1' AND status = 'BOOKED';
```

---

## JSON Query Examples (PostgreSQL)

```sql
-- Extract name from JSON
SELECT customer_info ->> 'name' AS customer_name
FROM actions
WHERE tenant_id = 'i10education_001';

-- Filter by JSON value
SELECT * FROM actions
WHERE action_data @> '{"status": "shipped"}'::jsonb
AND tenant_id = 'i10education_001';

-- Get array length
SELECT jsonb_array_length(order_items) AS item_count
FROM leads
WHERE tenant_id = 'i10education_001';
```

---

**Last Updated**: July 3, 2026  
**Version**: 1.0 (Perfect Assistant Phase 4)
