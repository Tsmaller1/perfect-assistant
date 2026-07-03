"""
SQLAlchemy ORM models for Perfect Assistant.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from database import Base


class Business(Base):
    """Business profile and settings."""
    __tablename__ = "businesses"

    tenant_id = Column(String(255), primary_key=True)
    business_name = Column(String(255), nullable=False)
    website_url = Column(String(512))
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(String(512))
    hours_of_operation = Column(JSON)  # {monday: "9-5", ...}
    description = Column(Text)
    services = Column(JSON)  # [{name, price, description}, ...]
    pricing = Column(JSON)  # [{service, price}, ...]
    faqs = Column(JSON)  # [{question, answer}, ...]
    social_media = Column(JSON)  # {facebook, instagram, linkedin, ...}
    ai_context = Column(Text)  # Formatted business knowledge for AI
    owner_phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = relationship("Appointment", back_populates="business")
    actions = relationship("Action", back_populates="business")
    conversations = relationship("Conversation", back_populates="business")
    leads = relationship("Lead", back_populates="business")

    __table_args__ = (
        Index("idx_businesses_tenant_id", "tenant_id"),
    )


class Appointment(Base):
    """Appointment bookings."""
    __tablename__ = "appointments"

    appointment_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(255), ForeignKey("businesses.tenant_id"), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255))
    customer_phone = Column(String(20))
    scheduled_datetime = Column(DateTime, nullable=False)
    service_type = Column(String(255), default="General")
    duration_minutes = Column(Integer, default=30)
    status = Column(String(50), default="BOOKED")  # BOOKED, CONFIRMED, COMPLETED, CANCELLED
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="appointments")

    __table_args__ = (
        Index("idx_appointments_tenant_id", "tenant_id"),
        Index("idx_appointments_scheduled_datetime", "scheduled_datetime"),
        Index("idx_appointments_status", "status"),
    )


class Action(Base):
    """Orders, appointments, leads, reservations."""
    __tablename__ = "actions"

    action_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(255), ForeignKey("businesses.tenant_id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # ORDER, APPOINTMENT, LEAD, RESERVATION
    customer_info = Column(JSON)  # {name, phone, email, ...}
    action_data = Column(JSON)  # {order_items, appointment_datetime, ...}
    status = Column(String(50), default="NEW")  # NEW, IN_PROGRESS, COMPLETED, FAILED
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="actions")

    __table_args__ = (
        Index("idx_actions_tenant_id", "tenant_id"),
        Index("idx_actions_action_type", "action_type"),
        Index("idx_actions_status", "status"),
        Index("idx_actions_created_at", "created_at"),
    )


class Conversation(Base):
    """Call transcripts and conversation memory."""
    __tablename__ = "conversations"

    conversation_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(255), ForeignKey("businesses.tenant_id"), nullable=False)
    call_sid = Column(String(255))
    customer_phone = Column(String(20))
    transcript = Column(JSON)  # [{role, text, timestamp}, ...]
    entities = Column(JSON)  # {name, email, phone, dates, ...}
    intent = Column(String(100))  # BOOK_APPOINTMENT, ASK_QUESTION, PLACE_ORDER, ...
    summary = Column(Text)
    outcome = Column(String(50))  # COMPLETED, TRANSFERRED, FAILED
    transferred_to_human = Column(Boolean, default=False)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="conversations")

    __table_args__ = (
        Index("idx_conversations_tenant_id", "tenant_id"),
        Index("idx_conversations_call_sid", "call_sid"),
        Index("idx_conversations_created_at", "created_at"),
    )


class Lead(Base):
    """Sales leads from payment handoffs."""
    __tablename__ = "leads"

    lead_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(255), ForeignKey("businesses.tenant_id"), nullable=False)
    call_sid = Column(String(255))
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20))
    customer_email = Column(String(255))
    order_value = Column(Float, default=0.0)
    order_items = Column(JSON)  # [{name, quantity, price}, ...]
    status = Column(String(50), default="PENDING")  # PENDING, AUTHORIZED, COMPLETED, FAILED, CONVERTED
    payment_status = Column(String(50))  # PENDING, AUTHORIZED, COMPLETED, FAILED
    payment_method = Column(String(100))
    amount = Column(Float)
    qualification_score = Column(Float, default=0.5)  # 0-1.0
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="leads")

    __table_args__ = (
        Index("idx_leads_tenant_id", "tenant_id"),
        Index("idx_leads_status", "status"),
        Index("idx_leads_qualification_score", "qualification_score"),
        Index("idx_leads_created_at", "created_at"),
    )


class Order(Base):
    """Orders (for backward compatibility with KDS)."""
    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(255), ForeignKey("businesses.tenant_id"), nullable=False)
    customer_name = Column(String(255))
    customer_phone = Column(String(20))
    items = Column(JSON)  # [{name, quantity, special_instructions}, ...]
    status = Column(String(50), default="NEW")  # NEW, PREPARATION, READY, PICKED_UP, CANCELLED
    total_price = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_orders_tenant_id", "tenant_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
    )
