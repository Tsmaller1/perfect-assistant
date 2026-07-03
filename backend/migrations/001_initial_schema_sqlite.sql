"""
SQL Migration: Create all tables for Perfect Assistant (SQLite - Development Only)
Target: SQLite 3.8+
Note: SQLite uses TEXT instead of JSONB, and doesn't support all PostgreSQL features
"""

-- ============================================================================
-- BUSINESSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS businesses (
    tenant_id TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    website_url TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    hours_of_operation TEXT,  -- JSON string
    description TEXT,
    services TEXT,  -- JSON string
    pricing TEXT,  -- JSON string
    faqs TEXT,  -- JSON string
    social_media TEXT,  -- JSON string
    ai_context TEXT,
    owner_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_businesses_tenant_id ON businesses(tenant_id);


-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    customer_phone TEXT,
    scheduled_datetime TIMESTAMP NOT NULL,
    service_type TEXT DEFAULT 'General',
    duration_minutes INTEGER DEFAULT 30,
    status TEXT DEFAULT 'BOOKED',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES businesses(tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_appointments_tenant_id ON appointments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_appointments_scheduled_datetime ON appointments(scheduled_datetime);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);


-- ============================================================================
-- ACTIONS TABLE (Orders, Appointments, Leads, Reservations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS actions (
    action_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    customer_info TEXT,  -- JSON string
    action_data TEXT,  -- JSON string
    status TEXT DEFAULT 'NEW',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES businesses(tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_actions_tenant_id ON actions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_actions_action_type ON actions(action_type);
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);
CREATE INDEX IF NOT EXISTS idx_actions_created_at ON actions(created_at);


-- ============================================================================
-- CONVERSATIONS TABLE (Call transcripts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    call_sid TEXT,
    customer_phone TEXT,
    transcript TEXT,  -- JSON string
    entities TEXT,  -- JSON string
    intent TEXT,
    summary TEXT,
    outcome TEXT,
    transferred_to_human INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES businesses(tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_tenant_id ON conversations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversations_call_sid ON conversations(call_sid);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);


-- ============================================================================
-- LEADS TABLE (Sales leads)
-- ============================================================================

CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    call_sid TEXT,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_email TEXT,
    order_value REAL DEFAULT 0.0,
    order_items TEXT,  -- JSON string
    status TEXT DEFAULT 'PENDING',
    payment_status TEXT,
    payment_method TEXT,
    amount REAL,
    qualification_score REAL DEFAULT 0.5,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES businesses(tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_leads_tenant_id ON leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_qualification_score ON leads(qualification_score);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);


-- ============================================================================
-- ORDERS TABLE (For KDS backward compatibility)
-- ============================================================================

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_name TEXT,
    customer_phone TEXT,
    items TEXT,  -- JSON string
    status TEXT DEFAULT 'NEW',
    total_price REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES businesses(tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_tenant_id ON orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
