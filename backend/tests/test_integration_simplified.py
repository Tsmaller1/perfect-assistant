"""
Simplified integration tests for Perfect Assistant backend.

Tests core database functionality:
- AppointmentManager operations
- ConversationMemory operations  
- PaymentHandoffManager operations
- ActionQueueManager operations
- Multi-tenant data isolation
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from appointments import AppointmentManager
from conversation_memory import ConversationMemory
from payment_handoff import PaymentHandoffManager
from action_queue import ActionQueueManager, ActionType, ActionStatus
from models import Appointment, Conversation, Lead, Action


# ============================================================================
# APPOINTMENT MANAGER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_book_appointment_persists_to_db(test_session, test_data):
    """Test that appointment is created and persisted to database."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    await manager.book_appointment(
        tenant_id=tenant_id,
        customer_name="TestCustomer",
        customer_email="test@example.com",
        customer_phone="+1-555-0000",
        scheduled_datetime=datetime(2026, 8, 1, 10, 0, 0),
        service_type="Dine-In",
        duration_minutes=60,
        notes="Test",
    )
    
    # Verify in database
    stmt = select(Appointment).where(
        Appointment.tenant_id == tenant_id,
        Appointment.customer_name == "TestCustomer",
    )
    result = await test_session.execute(stmt)
    appt = result.scalar_one_or_none()
    
    assert appt is not None
    assert appt.customer_name == "TestCustomer"


@pytest.mark.asyncio
async def test_get_appointments_returns_tenant_data(test_session, test_data):
    """Test retrieving appointments for a specific tenant."""
    manager = AppointmentManager(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Tenant 1 should have 2 appointments
    appts_t1 = await manager.get_appointments(tenant_id=tenant_1_id)
    assert len(appts_t1) == 2
    
    # Tenant 2 should have 0 appointments
    appts_t2 = await manager.get_appointments(tenant_id=tenant_2_id)
    assert len(appts_t2) == 0


@pytest.mark.asyncio
async def test_check_availability_detects_conflicts(test_session, test_data):
    """Test availability checking with conflict detection."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Existing appointments: July 10 at 2pm & 3pm
    # Try to book at 2pm (should conflict)
    available = await manager.check_availability(
        tenant_id=tenant_id,
        date_str="2026-07-10",
        start_time="14:00",
        duration_minutes=60,
    )
    assert available is False
    
    # Try to book at 12pm (should succeed)
    available = await manager.check_availability(
        tenant_id=tenant_id,
        date_str="2026-07-10",
        start_time="12:00",
        duration_minutes=120,
    )
    assert available is True


# ============================================================================
# CONVERSATION MEMORY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_conversation_persists(test_session, test_data):
    """Test creating a conversation persists to database."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.create_conversation(
        tenant_id=tenant_id,
        call_sid="CA_TEST_123",
        customer_phone="+1-555-9999",
    )
    
    conv_id = result.conversation_id
    
    # Verify in database
    stmt = select(Conversation).where(
        Conversation.tenant_id == tenant_id,
        Conversation.conversation_id == conv_id,
    )
    db_result = await test_session.execute(stmt)
    conv = db_result.scalar_one_or_none()
    
    assert conv is not None
    assert conv.customer_phone == "+1-555-9999"


@pytest.mark.asyncio
async def test_add_message_to_conversation(test_session, test_data):
    """Test adding messages to a conversation."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Create conversation
    conv = await manager.create_conversation(
        tenant_id=tenant_id,
        call_sid="CA_MSG_TEST",
        customer_phone="+1-555-1234",
    )
    
    # Add message
    updated_conv = await manager.add_message(
        tenant_id=tenant_id,
        conversation_id=conv.conversation_id,
        role="customer",
        text="I want a pizza",
        entities={"food": "pizza"},
    )
    
    # Verify message added
    assert len(updated_conv.transcript) == 1
    assert updated_conv.transcript[0]["text"] == "I want a pizza"


@pytest.mark.asyncio
async def test_get_recent_conversations(test_session, test_data):
    """Test retrieving recent conversations."""
    manager = ConversationMemory(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Tenant 1 has conversations
    t1_convs = await manager.get_recent_conversations(tenant_id=tenant_1_id)
    assert len(t1_convs) >= 1
    
    # Tenant 2 has no conversations
    t2_convs = await manager.get_recent_conversations(tenant_id=tenant_2_id)
    assert len(t2_convs) == 0


# ============================================================================
# PAYMENT HANDOFF TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_initiate_payment_handoff_persists(test_session, test_data):
    """Test creating a lead (payment handoff) persists to database."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    lead = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_LEAD_123",
        owner_phone="+1-555-0001",
        customer_name="LeadCustomer",
        customer_phone="+1-555-5555",
        customer_email="lead@example.com",
        order_value=200.00,
        order_items={"items": []},
        notes="Test lead",
    )
    
    # Verify in database
    stmt = select(Lead).where(
        Lead.tenant_id == tenant_id,
        Lead.lead_id == lead.lead_id,
    )
    result = await test_session.execute(stmt)
    db_lead = result.scalar_one_or_none()
    
    assert db_lead is not None
    assert db_lead.customer_name == "LeadCustomer"


@pytest.mark.asyncio
async def test_get_leads_multi_tenant_isolation(test_session, test_data):
    """Test that leads are isolated per tenant."""
    manager = PaymentHandoffManager(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Tenant 1 has leads
    t1_leads = await manager.get_leads(tenant_id=tenant_1_id)
    assert len(t1_leads) >= 1
    
    # Tenant 2 has no leads
    t2_leads = await manager.get_leads(tenant_id=tenant_2_id)
    assert len(t2_leads) == 0


@pytest.mark.asyncio
async def test_qualification_score_increases_with_value(test_session, test_data):
    """Test that qualification score increases with order value."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Low value lead
    low_lead = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_LOW",
        owner_phone="+1-555-0001",
        customer_name="LowValue",
        customer_phone="+1-555-1111",
        customer_email="low@example.com",
        order_value=20.00,
        order_items={},
        notes="",
    )
    
    # High value lead
    high_lead = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_HIGH",
        owner_phone="+1-555-0001",
        customer_name="HighValue",
        customer_phone="+1-555-2222",
        customer_email="high@example.com",
        order_value=500.00,
        order_items={},
        notes="",
    )
    
    # Higher value should have higher score
    assert high_lead.qualification_score > low_lead.qualification_score


# ============================================================================
# ACTION QUEUE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_broadcast_action_persists(test_session, test_data):
    """Test that actions are persisted to database."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    action = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.ORDER,
        customer_info={"name": "ActionCustomer"},
        action_data={"items": []},
    )
    
    # Verify in database
    stmt = select(Action).where(
        Action.tenant_id == tenant_id,
        Action.action_id == action.action_id,
    )
    result = await test_session.execute(stmt)
    db_action = result.scalar_one_or_none()
    
    assert db_action is not None
    assert db_action.action_type == ActionType.ORDER


@pytest.mark.asyncio
async def test_update_action_status(test_session, test_data):
    """Test updating action status."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Create action
    action = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.ORDER,
        customer_info={},
        action_data={},
    )
    
    # Update status
    updated = await manager.update_action_status(
        tenant_id=tenant_id,
        action_id=action.action_id,
        new_status=ActionStatus.COMPLETED,
        notes="Done",
    )
    
    assert updated.status == ActionStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_recent_actions_multi_tenant(test_session, test_data):
    """Test that actions are isolated per tenant."""
    manager = ActionQueueManager(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Tenant 1 has actions
    t1_actions = await manager.get_recent_actions(tenant_id=tenant_1_id)
    assert len(t1_actions) >= 1
    
    # Tenant 2 has no actions
    t2_actions = await manager.get_recent_actions(tenant_id=tenant_2_id)
    assert len(t2_actions) == 0


# ============================================================================
# DATABASE ISOLATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_multi_tenant_data_isolation(test_session, test_data):
    """Comprehensive multi-tenant isolation test."""
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # All tenant 1 data should be isolated from tenant 2
    stmt_appts = select(Appointment).where(Appointment.tenant_id == tenant_2_id)
    appts = (await test_session.execute(stmt_appts)).scalars().all()
    assert len(appts) == 0, "Tenant 2 should have no appointments"
    
    stmt_convs = select(Conversation).where(Conversation.tenant_id == tenant_2_id)
    convs = (await test_session.execute(stmt_convs)).scalars().all()
    assert len(convs) == 0, "Tenant 2 should have no conversations"
    
    stmt_leads = select(Lead).where(Lead.tenant_id == tenant_2_id)
    leads = (await test_session.execute(stmt_leads)).scalars().all()
    assert len(leads) == 0, "Tenant 2 should have no leads"
    
    # Tenant 1 should have data
    stmt_appts_t1 = select(Appointment).where(Appointment.tenant_id == tenant_1_id)
    appts_t1 = (await test_session.execute(stmt_appts_t1)).scalars().all()
    assert len(appts_t1) >= 2, "Tenant 1 should have appointments"


@pytest.mark.asyncio
async def test_transaction_commit(test_session, test_data):
    """Test that changes are properly committed."""
    tenant_id = test_data["tenant_1_id"]
    
    manager = AppointmentManager(test_session)
    
    # Create appointment
    await manager.book_appointment(
        tenant_id=tenant_id,
        customer_name="CommitTest",
        customer_email="commit@example.com",
        customer_phone="+1-555-7777",
        scheduled_datetime=datetime(2026, 9, 1, 10, 0, 0),
        service_type="Test",
        duration_minutes=30,
        notes="Commit test",
    )
    
    # Verify it persists immediately (without additional commit)
    stmt = select(Appointment).where(
        Appointment.customer_name == "CommitTest"
    )
    result = await test_session.execute(stmt)
    appt = result.scalar_one_or_none()
    
    assert appt is not None


@pytest.mark.asyncio
async def test_same_customer_multiple_records(test_session, test_data):
    """Test that same customer can have multiple records."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Create 2 appointments for same customer
    await manager.book_appointment(
        tenant_id=tenant_id,
        customer_name="Repeat",
        customer_email="repeat@example.com",
        customer_phone="+1-555-8888",
        scheduled_datetime=datetime(2026, 9, 5, 10, 0, 0),
        service_type="A",
        duration_minutes=30,
        notes="First",
    )
    
    await manager.book_appointment(
        tenant_id=tenant_id,
        customer_name="Repeat",
        customer_email="repeat@example.com",
        customer_phone="+1-555-8888",
        scheduled_datetime=datetime(2026, 9, 10, 14, 0, 0),
        service_type="B",
        duration_minutes=45,
        notes="Second",
    )
    
    # Should have both
    stmt = select(Appointment).where(
        Appointment.tenant_id == tenant_id,
        Appointment.customer_name == "Repeat",
    )
    results = (await test_session.execute(stmt)).scalars().all()
    assert len(results) == 2
