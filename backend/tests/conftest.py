"""
Pytest configuration and fixtures for Perfect Assistant backend integration tests.

Provides:
- Database fixtures (SQLite for testing)
- Async session fixtures
- Manager instance fixtures
- Multi-tenant test data
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import models
from models import Base, Business, Appointment, Conversation, Lead, Action, Order


# Database configuration for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests."""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create an async session for testing."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_data(test_session):
    """Create test data: two tenants with sample data."""
    # Tenant 1 business
    business_1 = Business(
        tenant_id="tenant-1",
        business_name="Test Pizza Shop",
        phone="+1-800-PIZZA-1",
        owner_phone="+1-555-0001",
        ai_context="Handle pizza orders and reservations",
        hours_of_operation={"mon": "10am-10pm", "tue": "10am-10pm"},
    )
    
    # Tenant 2 business
    business_2 = Business(
        tenant_id="tenant-2",
        business_name="Test Coffee Shop",
        phone="+1-800-COFFEE-1",
        owner_phone="+1-555-0002",
        ai_context="Handle coffee orders",
        hours_of_operation={"mon": "6am-6pm", "tue": "6am-6pm"},
    )
    
    test_session.add(business_1)
    test_session.add(business_2)
    
    # Sample appointments for tenant 1
    appt_1 = Appointment(
        tenant_id="tenant-1",
        appointment_id="appt-001",
        customer_name="Alice",
        customer_email="alice@example.com",
        customer_phone="+1-555-1001",
        scheduled_datetime=datetime(2026, 7, 10, 14, 0, 0),
        service_type="Dine-In",
        duration_minutes=60,
        status="CONFIRMED",
        notes="Party of 4",
    )
    
    appt_2 = Appointment(
        tenant_id="tenant-1",
        appointment_id="appt-002",
        customer_name="Bob",
        customer_email="bob@example.com",
        customer_phone="+1-555-1002",
        scheduled_datetime=datetime(2026, 7, 10, 15, 0, 0),
        service_type="Delivery",
        duration_minutes=45,
        status="CONFIRMED",
        notes="Large order",
    )
    
    # Sample conversation for tenant 1
    conversation_1 = Conversation(
        tenant_id="tenant-1",
        conversation_id="conv-001",
        call_sid="CA1234567890abcdef",
        customer_phone="+1-555-2001",
        transcript=[
            {"role": "customer", "text": "I'd like to order a pizza"},
            {"role": "ai", "text": "What size would you like?"},
            {"role": "customer", "text": "Large with pepperoni"},
        ],
        entities={"order_type": "PIZZA", "size": "LARGE"},
        intent="ORDER",
        outcome="COMPLETED",
    )
    
    # Sample lead for tenant 1
    lead_1 = Lead(
        tenant_id="tenant-1",
        lead_id="lead-001",
        call_sid="CA0987654321fedcba",
        customer_name="Charlie",
        customer_email="charlie@example.com",
        customer_phone="+1-555-3001",
        order_value=150.00,
        order_items={"items": [{"name": "Pizza", "qty": 2}]},
        status="QUALIFIED",
        payment_status="PENDING",
        qualification_score=0.85,
    )
    
    # Sample action for tenant 1
    action_1 = Action(
        tenant_id="tenant-1",
        action_id="action-001",
        action_type="ORDER",
        customer_info={"name": "David", "phone": "+1-555-4001"},
        action_data={"items": [{"name": "Pasta", "qty": 1}]},
        status="NEW",
    )
    
    test_session.add_all([appt_1, appt_2, conversation_1, lead_1, action_1])
    
    await test_session.commit()
    
    return {
        "tenant_1_id": "tenant-1",
        "tenant_2_id": "tenant-2",
        "business_1": business_1,
        "business_2": business_2,
    }
