# Perfect Assistant — Database Schema

## Overview
PostgreSQL schema for multi-tenant Perfect Assistant platform.

## Tables

### businesses
```sql
CREATE TABLE businesses (
    tenant_id UUID PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    website_url VARCHAR(1024) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    address TEXT,
    hours JSONB,  -- {"monday": "9-5", "tuesday": "9-5", ...}
    
    scraped_data JSONB,  -- Full scraped website data
    ai_context TEXT,     -- Formatted for AI system prompt
    
    owner_email VARCHAR(255),
    owner_phone VARCHAR(20),
    
    ai_mode_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_businesses_phone ON businesses(phone_number);
```

### appointments
```sql
CREATE TABLE appointments (
    appointment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_phone VARCHAR(20),
    
    scheduled_datetime TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    service_type VARCHAR(255),
    
    status VARCHAR(50) DEFAULT 'BOOKED',  -- BOOKED, CONFIRMED, COMPLETED, CANCELLED
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appointments_tenant ON appointments(tenant_id);
CREATE INDEX idx_appointments_datetime ON appointments(scheduled_datetime);
CREATE INDEX idx_appointments_status ON appointments(status);
```

### actions
```sql
CREATE TABLE actions (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    
    action_type VARCHAR(50) NOT NULL,  -- ORDER, APPOINTMENT, LEAD, RESERVATION
    
    customer_info JSONB,  -- {name, email, phone, etc.}
    action_data JSONB,    -- Flexible data per action type
    
    status VARCHAR(50) DEFAULT 'NEW',  -- NEW, IN_PROGRESS, COMPLETED, FAILED
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_actions_tenant ON actions(tenant_id);
CREATE INDEX idx_actions_type ON actions(action_type);
CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_actions_created ON actions(created_at DESC);
```

### conversations
```sql
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    
    call_sid VARCHAR(255) NOT NULL,  -- Twilio call ID
    customer_phone VARCHAR(20),
    
    transcript TEXT,
    intent VARCHAR(255),  -- BOOK_APPOINTMENT, ASK_QUESTION, PLACE_ORDER, etc.
    entities JSONB,       -- Extracted data {name, email, date, items, etc.}
    
    ai_handled BOOLEAN DEFAULT TRUE,
    transferred_to_human BOOLEAN DEFAULT FALSE,
    outcome VARCHAR(50),  -- SUCCESS, PARTIAL, TRANSFERRED, FAILED
    
    duration_seconds INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);
CREATE INDEX idx_conversations_call_sid ON conversations(call_sid);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
```

### leads
```sql
CREATE TABLE leads (
    lead_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),
    customer_email VARCHAR(255),
    
    qualification_score FLOAT DEFAULT 0.5,  -- 0-1 rating
    notes TEXT,
    
    status VARCHAR(50) DEFAULT 'NEW',  -- NEW, CONTACTED, CONVERTED, LOST
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leads_tenant ON leads(tenant_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_phone ON leads(customer_phone);
```

### orders (Deprecated - use actions table with type='ORDER')
```sql
-- For backward compatibility with existing KDS system
-- New orders should use actions table instead
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),
    
    items JSONB,  -- [{name, quantity, customization}, ...]
    special_instructions TEXT,
    
    status VARCHAR(50) DEFAULT 'OPEN',  -- OPEN, IN_PROGRESS, COMPLETE, CANCELLED
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_tenant ON orders(tenant_id);
CREATE INDEX idx_orders_status ON orders(status);
```

---

## Views (Optional but useful)

### Today's Business Summary
```sql
CREATE VIEW business_daily_summary AS
SELECT 
    b.tenant_id,
    b.business_name,
    COUNT(DISTINCT c.conversation_id) as calls_today,
    COUNT(DISTINCT CASE WHEN c.ai_handled THEN c.conversation_id END) as ai_handled_calls,
    COUNT(DISTINCT a.appointment_id) as appointments_today,
    COUNT(DISTINCT CASE WHEN ac.action_type = 'ORDER' THEN ac.action_id END) as orders_today,
    COUNT(DISTINCT CASE WHEN ac.action_type = 'LEAD' THEN ac.action_id END) as leads_today
FROM 
    businesses b
    LEFT JOIN conversations c ON b.tenant_id = c.tenant_id AND DATE(c.created_at) = CURRENT_DATE
    LEFT JOIN appointments a ON b.tenant_id = a.tenant_id AND DATE(a.scheduled_datetime) = CURRENT_DATE
    LEFT JOIN actions ac ON b.tenant_id = ac.tenant_id AND DATE(ac.created_at) = CURRENT_DATE
GROUP BY b.tenant_id, b.business_name;
```

---

## Setup SQL

```sql
-- Create database
CREATE DATABASE perfect_assistant;

-- Connect to database
\c perfect_assistant

-- Create tables (run all CREATE TABLE statements above)
-- Create views (run VIEW statements above)

-- Create basic indexes
VACUUM ANALYZE;
```

---

## Seed Data Example

```sql
INSERT INTO businesses (
    tenant_id, business_name, website_url, phone_number, 
    address, owner_email, hours
) VALUES (
    gen_random_uuid(),
    'I10 Education',
    'https://i10education.com',
    '+15559990000',
    '123 Main St, City, State',
    'owner@i10education.com',
    jsonb_build_object(
        'monday', '9:00-17:00',
        'tuesday', '9:00-17:00',
        'wednesday', '9:00-17:00',
        'thursday', '9:00-17:00',
        'friday', '9:00-17:00',
        'saturday', 'CLOSED',
        'sunday', 'CLOSED'
    )
);
```
