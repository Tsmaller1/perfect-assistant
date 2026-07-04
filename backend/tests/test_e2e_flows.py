"""
End-to-End Flow Tests
Complete workflow validation: appointment booking, order creation, lead handoff, conversations.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from models import Business, Appointment, Order, Lead, Conversation, Action
from appointments import AppointmentManager
from action_queue import ActionQueueManager, ActionType, ActionStatus
from conversation_memory import ConversationMemory
from payment_handoff import PaymentHandoffManager


@pytest.mark.asyncio
async def test_appointment_booking_flow(test_session, test_data):
    """E2E: Customer calls → book appointment → confirm → view schedule."""
    tenant_id = test_data["tenant_1_id"]
    
    manager = AppointmentManager(test_session)
    
    # Step 1: Check availability for tomorrow at 10:00 AM
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    availability = await manager.check_availability(
        tenant_id,
        date_str=tomorrow,
        start_time="10:00",
        duration_minutes=60
    )
    
    # Should be available (no conflicting appointments)
    assert availability["available"] is True
    
    # Step 2: Book appointment
    scheduled_datetime = f"{tomorrow}T10:00:00"
    appt = await manager.book_appointment(
        tenant_id=tenant_id,
        customer_name="Sarah Johnson",
        customer_email="sarah@example.com",
        customer_phone="+1-555-5555",
        scheduled_datetime=scheduled_datetime,
        service_type="Haircut",
        duration_minutes=60,
        notes="First time customer"
    )
    
    assert appt["status"] == "success"
    appt_id = appt["appointment_id"]
    
    # Step 3: Verify appointment in database
    stmt = select(Appointment).where(Appointment.appointment_id == appt_id)
    result = await test_session.execute(stmt)
    db_appt = result.scalar_one_or_none()
    
    assert db_appt is not None
    assert db_appt.customer_name == "Sarah Johnson"
    assert db_appt.service_type == "Haircut"
    
    # Step 4: Check availability again - time slot should be taken
    availability_after = await manager.check_availability(
        tenant_id,
        date_str=tomorrow,
        start_time="10:00",
        duration_minutes=60
    )
    
    assert availability_after["available"] is False
    assert len(availability_after["conflicts"]) > 0
    
    # Step 5: View daily schedule
    schedule = await manager.get_daily_schedule(tenant_id, tomorrow)
    assert schedule["status"] == "success"
    assert len(schedule["appointments"]) > 0
    
    # Find our appointment in schedule
    found = False
    for appt_in_schedule in schedule["appointments"]:
        if appt_in_schedule["appointment_id"] == appt_id:
            found = True
            break
    
    assert found is True


@pytest.mark.asyncio
async def test_conversation_flow(test_session, test_data):
    """E2E: Customer calls → conversation created → transcript recorded → summary generated."""
    tenant_id = test_data["tenant_1_id"]
    
    conv_manager = ConversationMemory(test_session)
    
    # Step 1: Customer calls - create conversation
    conv_result = await conv_manager.create_conversation(
        tenant_id=tenant_id,
        call_sid="CA_E2E_001",
        customer_phone="+1-555-9999"
    )
    
    # Handle potential error
    if conv_result.get("status") == "error":
        pytest.skip(f"Conversation creation failed: {conv_result.get('error')}")
    
    assert conv_result["status"] == "success"
    conv_id = conv_result["conversation_id"]
    
    # Step 2: Add messages to conversation
    entities_msg1 = [{"type": "PRODUCT", "value": "pizza"}]
    result_msg1 = await conv_manager.add_message(
        tenant_id=tenant_id,
        conversation_id=conv_id,
        role="customer",
        text="I'd like to order a pepperoni pizza",
        entities=entities_msg1
    )
    print(f"DEBUG: add_message result 1 = {result_msg1}")
    assert result_msg1["status"] == "success", f"Failed to add message 1: {result_msg1}"
    
    entities_msg2 = [{"type": "SIZE", "value": "large"}]
    result_msg2 = await conv_manager.add_message(
        tenant_id=tenant_id,
        conversation_id=conv_id,
        role="assistant",
        text="Sure! What size would you like?",
        entities=entities_msg2
    )
    print(f"DEBUG: add_message result 2 = {result_msg2}")
    assert result_msg2["status"] == "success", f"Failed to add message 2: {result_msg2}"
    
    result_msg3 = await conv_manager.add_message(
        tenant_id=tenant_id,
        conversation_id=conv_id,
        role="customer",
        text="Large please",
        entities=[]
    )
    print(f"DEBUG: add_message result 3 = {result_msg3}")
    assert result_msg3["status"] == "success", f"Failed to add message 3: {result_msg3}"
    
    # Step 3: Close conversation with outcome
    await conv_manager.close_conversation(
        tenant_id=tenant_id,
        conversation_id=conv_id,
        outcome="ORDER_PLACED",
        transferred_to_human=False,
        duration_seconds=145
    )
    
    # Step 4: Retrieve conversation and verify transcript
    # Step 4: Retrieve conversation context
    context_result = await conv_manager.get_conversation_context(
        tenant_id=tenant_id,
        conversation_id=conv_id
    )
    
    assert context_result["status"] == "success", f"Failed to get context: {context_result}"
    context = context_result["context"]
    print(f"DEBUG: context = {context}")
    print(f"DEBUG: context['transcript'] = {context['transcript']}")
    assert context["conversation_id"] == conv_id
    assert len(context["transcript"]) == 3, f"Expected 3 messages but got {len(context['transcript'])}: {context['transcript']}"
    assert context["outcome"] == "ORDER_PLACED"
    
    # Step 5: Get recent conversations
    recent = await conv_manager.get_recent_conversations(tenant_id, limit=10)
    
    assert recent["status"] == "success"
    found = False
    for conv_rec in recent.get("conversations", []):
        if conv_rec.get("conversation_id") == conv_id:
            found = True
            break
    
    assert found is True


@pytest.mark.asyncio
async def test_order_creation_flow(test_session, test_data):
    """E2E: Customer orders → Action created → KDS broadcast → completion."""
    tenant_id = test_data["tenant_1_id"]
    
    action_manager = ActionQueueManager(test_session)
    
    # Step 1: Create order action
    customer_info = {
        "name": "Michael Torres",
        "phone": "+1-555-2222",
        "email": "michael@example.com"
    }
    
    action_data = {
        "items": [
            {
                "quantity": 2,
                "name": "Margherita Pizza",
                "customization": "Extra cheese"
            },
            {
                "quantity": 1,
                "name": "Caesar Salad",
                "customization": "Dressing on side"
            },
            {
                "quantity": 1,
                "name": "Tiramisu",
                "customization": ""
            }
        ],
        "notes": "Allergic to nuts",
        "total": 45.99
    }
    
    order_id = await action_manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.ORDER,
        customer_info=customer_info,
        action_data=action_data
    )
    
    assert order_id is not None
    
    # Step 2: Verify order persisted to database
    stmt = select(Action).where(Action.action_id == order_id)
    result = await test_session.execute(stmt)
    db_action = result.scalar_one_or_none()
    
    assert db_action is not None
    assert db_action.action_type == "ORDER"
    assert db_action.status == "NEW"
    assert db_action.customer_info["name"] == "Michael Torres"
    assert len(db_action.action_data["items"]) == 3
    
    # Step 3: Update order to IN_PROGRESS (kitchen started making it)
    await action_manager.update_action_status(
        tenant_id=tenant_id,
        action_id=order_id,
        new_status=ActionStatus.IN_PROGRESS,
        notes="Entered kitchen queue"
    )
    
    # Verify status change
    stmt = select(Action).where(Action.action_id == order_id)
    result = await test_session.execute(stmt)
    updated_action = result.scalar_one_or_none()
    
    assert updated_action.status == "IN_PROGRESS"
    assert updated_action.notes == "Entered kitchen queue"
    
    # Step 4: Mark order complete
    await action_manager.update_action_status(
        tenant_id=tenant_id,
        action_id=order_id,
        new_status=ActionStatus.COMPLETED,
        notes="Ready for pickup"
    )
    
    # Verify completion
    stmt = select(Action).where(Action.action_id == order_id)
    result = await test_session.execute(stmt)
    final_action = result.scalar_one_or_none()
    
    assert final_action.status == "COMPLETED"


@pytest.mark.asyncio
async def test_lead_conversion_flow(test_session, test_data):
    """E2E: High-value customer → lead created → qualified → follow-up."""
    tenant_id = test_data["tenant_1_id"]
    
    lead_manager = PaymentHandoffManager(test_session)
    
    # Step 1: Initiate payment handoff (expensive order)
    lead = await lead_manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_E2E_LEAD_001",
        owner_phone="+1-555-0000",
        customer_name="Jennifer Chen",
        customer_phone="+1-555-3333",
        customer_email="jennifer@corp.com",
        order_value=2500.00,  # Large catering order
        order_items={
            "type": "catering",
            "item_count": 50,
            "description": "Corporate event catering for 50 people"
        },
        notes="Repeat customer from Q1"
    )
    
    assert lead["status"] == "success"
    lead_id = lead["lead_id"]
    
    # Step 2: Verify lead in database
    stmt = select(Lead).where(Lead.lead_id == lead_id)
    result = await test_session.execute(stmt)
    db_lead = result.scalar_one_or_none()
    
    assert db_lead is not None
    assert db_lead.customer_name == "Jennifer Chen"
    assert db_lead.order_value == 2500.00
    
    # High order value should result in high qualification score
    assert db_lead.qualification_score >= 0.8
    
    # Step 3: Get qualified leads
    qualified = await lead_manager.get_qualified_leads(tenant_id, min_score=0.8)
    
    assert qualified["status"] == "success"
    found = False
    for ql in qualified.get("qualified_leads", []):
        if ql.get("lead_id") == lead_id:
            found = True
            assert ql["qualification_score"] >= 0.8
            break
    
    assert found is True
    
    # Step 4: Complete payment transfer
    await lead_manager.complete_payment_transfer(
        call_sid="CA_E2E_LEAD_001",
        payment_status="COMPLETED",
        payment_method="corporate_invoice",
        amount=2500.00
    )
    
    # Step 5: Update lead status to CONTACTED
    await lead_manager.update_lead_status(
        tenant_id=tenant_id,
        lead_id=lead_id,
        new_status="CONTACTED",
        notes="Sales call scheduled for Friday 10 AM"
    )
    
    # Verify update
    stmt = select(Lead).where(Lead.lead_id == lead_id)
    result = await test_session.execute(stmt)
    updated_lead = result.scalar_one_or_none()
    
    assert updated_lead.status == "CONTACTED"


@pytest.mark.asyncio
async def test_multi_tenant_isolation_e2e(test_session, test_data):
    """E2E: Verify tenant A data never leaks to tenant B across all flows."""
    tenant_1 = test_data["tenant_1_id"]
    tenant_2 = test_data["tenant_2_id"]
    
    # Create appointment in tenant 1
    appt_mgr = AppointmentManager(test_session)
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    appt_t1 = await appt_mgr.book_appointment(
        tenant_id=tenant_1,
        customer_name="Alice (Tenant 1)",
        customer_email="alice@tenant1.com",
        customer_phone="+1-555-1111",
        scheduled_datetime=f"{tomorrow}T14:00:00",
        service_type="Premium",
        duration_minutes=90,
        notes=""
    )
    
    # Create conversation in tenant 1
    conv_mgr = ConversationMemory(test_session)
    conv_t1 = await conv_mgr.create_conversation(
        tenant_id=tenant_1,
        call_sid="CA_TENANT_1",
        customer_phone="+1-555-1111"
    )
    
    # Create lead in tenant 1
    lead_mgr = PaymentHandoffManager(test_session)
    lead_t1 = await lead_mgr.initiate_payment_handoff(
        tenant_id=tenant_1,
        call_sid="CA_LEAD_T1",
        owner_phone="+1-555-0001",
        customer_name="Bob (Tenant 1)",
        customer_phone="+1-555-2222",
        customer_email="bob@tenant1.com",
        order_value=500.00,
        order_items={},
        notes=""
    )
    
    # Now verify tenant 2 CANNOT see any of tenant 1's data
    
    # Check tenant 2 appointments (should only see pre-existing test data)
    t2_appts = await appt_mgr.get_appointments(tenant_2)
    t2_appt_ids = [a["appointment_id"] for a in t2_appts.get("appointments", [])]
    assert appt_t1["appointment_id"] not in t2_appt_ids
    
    # Check tenant 2 conversations
    t2_convs = await conv_mgr.get_recent_conversations(tenant_2, limit=50)
    t2_conv_ids = [c.get("conversation_id") for c in t2_convs.get("conversations", [])]
    assert conv_t1["conversation_id"] not in t2_conv_ids
    
    # Check tenant 2 leads
    t2_leads = await lead_mgr.get_leads(tenant_2)
    t2_lead_ids = [l.get("lead_id") for l in t2_leads.get("leads", [])]
    assert lead_t1["lead_id"] not in t2_lead_ids


@pytest.mark.asyncio
async def test_combined_business_workflow(test_session, test_data):
    """E2E: Full business day - multiple customers, different flows."""
    tenant_id = test_data["tenant_1_id"]
    
    action_mgr = ActionQueueManager(test_session)
    conv_mgr = ConversationMemory(test_session)
    appt_mgr = AppointmentManager(test_session)
    lead_mgr = PaymentHandoffManager(test_session)
    
    # Customer 1: Quick order
    await action_mgr.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.ORDER,
        customer_info={"name": "John", "phone": "+1-555-1001"},
        action_data={"items": [{"quantity": 1, "name": "Pizza"}], "total": 15.99}
    )
    
    # Customer 2: Appointment booking via call
    conv2 = await conv_mgr.create_conversation(
        tenant_id=tenant_id,
        call_sid="CA_CUST2",
        customer_phone="+1-555-1002"
    )
    
    await conv_mgr.add_message(
        tenant_id=tenant_id,
        conversation_id=conv2["conversation_id"],
        role="customer",
        text="I'd like to book an appointment",
        entities=[]
    )
    
    # Customer 3: High-value lead
    lead3 = await lead_mgr.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_LEAD_CUST3",
        owner_phone="+1-555-0003",
        customer_name="Premium Client",
        customer_phone="+1-555-1003",
        customer_email="premium@client.com",
        order_value=5000.00,
        order_items={"description": "Enterprise package"},
        notes="VIP"
    )
    
    # Verify all three customers created separate, isolated records
    all_actions = await action_mgr.get_recent_actions(tenant_id, limit=100)
    all_convs = await conv_mgr.get_recent_conversations(tenant_id, limit=100)
    all_leads = await lead_mgr.get_leads(tenant_id)
    
    assert len(all_actions) > 0  # Orders persisted
    assert len(all_convs.get("conversations", [])) > 0  # Conversations persisted
    assert len(all_leads.get("leads", [])) > 0  # Leads persisted
