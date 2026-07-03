-- Phase 4.5: Add Dashboard Configuration Fields
-- Adds twilio_number and ai_mode_enabled to businesses table

ALTER TABLE businesses
ADD COLUMN twilio_number VARCHAR(20),
ADD COLUMN ai_mode_enabled BOOLEAN DEFAULT TRUE;

-- Create index for ai_mode lookups
CREATE INDEX idx_businesses_ai_mode ON businesses(ai_mode_enabled);
