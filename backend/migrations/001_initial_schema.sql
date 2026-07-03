"""
SQL Migration: Create all tables for Perfect Assistant.
Target: PostgreSQL 12+
"""

-- ============================================================================
-- BUSINESSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS businesses (
    tenant_id VARCHAR(255) PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    website_url VARCHAR(512),
    phone VARCHAR(20),
    email VARCHAR(255),
    address VARCHAR(512),
    hours_of_operation JSONB,
    description TEXT,
    services JSONB,
    pricing JSONB,
    faqs JSONB,
    social_media JSONB,
    ai_context TEXT,
    owner_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_businesses_tenant_id ON businesses(tenant_id);


-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_phone VARCHAR(20),
    scheduled_datetime TIMESTAMP NOT NULL,
    service_type VARCHAR(255) DEFAULT 'General',
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR(50) DEFAULT 'BOOKED',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appointments_tenant_id ON appointments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_appointments_scheduled_datetime ON appointments(scheduled_datetime);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);


-- ============================================================================
-- ACTIONS TABLE (Orders, Appointments, Leads, Reservations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS actions (
    action_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    customer_info JSONB,
    action_data JSONB,
    status VARCHAR(50) DEFAULT 'NEW',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_actions_tenant_id ON actions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_actions_action_type ON actions(action_type);
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);
CREATE INDEX IF NOT EXISTS idx_actions_created_at ON actions(created_at);


-- ============================================================================
-- CONVERSATIONS TABLE (Call transcripts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    call_sid VARCHAR(255),
    customer_phone VARCHAR(20),
    transcript JSONB,
    entities JSONB,
    intent VARCHAR(100),
    summary TEXT,
    outcome VARCHAR(50),
    transferred_to_human BOOLEAN DEFAULT FALSE,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_tenant_id ON conversations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversations_call_sid ON conversations(call_sid);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);


-- ============================================================================
-- LEADS TABLE (Sales leads)
-- ============================================================================

CREATE TABLE IF NOT EXISTS leads (
    lead_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    call_sid VARCHAR(255),
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20),
    customer_email VARCHAR(255),
    order_value FLOAT DEFAULT 0.0,
    order_items JSONB,
    status VARCHAR(50) DEFAULT 'PENDING',
    payment_status VARCHAR(50),
    payment_method VARCHAR(100),
    amount FLOAT,
    qualification_score FLOAT DEFAULT 0.5,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leads_tenant_id ON leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_qualification_score ON leads(qualification_score);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);


-- ============================================================================
-- ORDERS TABLE (For KDS backward compatibility)
-- ============================================================================

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES businesses(tenant_id) ON DELETE CASCADE,
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),
    items JSONB,
    status VARCHAR(50) DEFAULT 'NEW',
    total_price FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_tenant_id ON orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);


-- ============================================================================
-- MATERIALIZED VIEW: Daily Summary (Optional)
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS business_daily_summary AS
SELECT
    tenant_id,
    DATE(created_at) as date,
    COUNT(DISTINCT CASE WHEN action_type = 'ORDER' THEN action_id END) as orders_count,
    COUNT(DISTINCT CASE WHEN action_type = 'APPOINTMENT' THEN action_id END) as appointments_count,
    COUNT(DISTINCT CASE WHEN action_type = 'LEAD' THEN action_id END) as leads_count,
    COUNT(DISTINCT conversation_id) as conversations_count,
    COALESCE(SUM(CASE WHEN action_type = 'ORDER' THEN (action_data->>'total_price')::FLOAT END), 0) as total_revenue
FROM
    (SELECT tenant_id, created_at, action_type, action_id, NULL::VARCHAR as conversation_id, NULL::JSONB as action_data FROM actions
     UNION ALL
     SELECT tenant_id, created_at, NULL::VARCHAR, NULL::VARCHAR, conversation_id, NULL::JSONB FROM conversations) combined
GROUP BY
    tenant_id, DATE(created_at);

CREATE INDEX IF NOT EXISTS idx_daily_summary_tenant_date ON business_daily_summary(tenant_id, date);
