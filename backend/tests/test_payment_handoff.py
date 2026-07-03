"""
Integration tests for PaymentHandoffManager (Lead Management).

Tests:
- Lead creation with qualification scoring
- Lead status updates
- Payment handoff completion
- Lead filtering by qualification score
- Multi-tenant isolation
"""

import pytest
from payment_handoff import PaymentHandoffManager


@pytest.mark.asyncio
async def test_initiate_payment_handoff(test_session, test_data):
    """Test initiating a payment handoff (creating a lead)."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_HANDOFF_001",
        owner_phone="+1-555-0001",
        customer_name="Frank",
        customer_phone="+1-555-7001",
        customer_email="frank@example.com",
        order_value=200.00,
        order_items={"items": [{"name": "Premium Package", "qty": 1}]},
        notes="High-value lead",
    )
    
    assert result["status"] == "success"
    assert result["lead"]["customer_name"] == "Frank"
    assert result["lead"]["status"] == "NEW"
    # Higher order value = higher qualification score
    assert result["lead"]["qualification_score"] > 0.5


@pytest.mark.asyncio
async def test_qualification_score_calculation(test_session, test_data):
    """Test that qualification score increases with order value."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Low value lead
    low_result = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_LOW_VALUE",
        owner_phone="+1-555-0001",
        customer_name="Grace",
        customer_phone="+1-555-7002",
        customer_email="grace@example.com",
        order_value=20.00,
        order_items={"items": [{"name": "Drink", "qty": 1}]},
        notes="Low value",
    )
    
    # High value lead
    high_result = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_HIGH_VALUE",
        owner_phone="+1-555-0001",
        customer_name="Henry",
        customer_phone="+1-555-7003",
        customer_email="henry@example.com",
        order_value=500.00,
        order_items={"items": [{"name": "Catering", "qty": 2}]},
        notes="High value",
    )
    
    low_score = low_result["lead"]["qualification_score"]
    high_score = high_result["lead"]["qualification_score"]
    
    # High value lead should have higher score
    assert high_score > low_score


@pytest.mark.asyncio
async def test_complete_payment_transfer(test_session, test_data):
    """Test completing a payment transfer."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Create a lead first
    create_result = await manager.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid="CA_PAYMENT_001",
        owner_phone="+1-555-0001",
        customer_name="Iris",
        customer_phone="+1-555-7004",
        customer_email="iris@example.com",
        order_value=150.00,
        order_items={},
        notes="",
    )
    
    # Complete the payment
    result = await manager.complete_payment_transfer(
        call_sid="CA_PAYMENT_001",
        payment_status="COMPLETED",
        payment_method="CREDIT_CARD",
        amount=150.00,
    )
    
    assert result["status"] == "success"
    assert result["lead"]["payment_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_get_leads(test_session, test_data):
    """Test retrieving leads for a tenant."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.get_leads(tenant_id=tenant_id)
    
    assert result["status"] == "success"
    assert len(result["leads"]) >= 1
    assert all(lead["tenant_id"] == tenant_id for lead in result["leads"])


@pytest.mark.asyncio
async def test_get_qualified_leads(test_session, test_data):
    """Test retrieving high-qualification leads."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # lead-001 has score 0.85
    result = await manager.get_qualified_leads(
        tenant_id=tenant_id,
        min_score=0.7,
    )
    
    assert result["status"] == "success"
    assert len(result["leads"]) >= 1
    assert all(lead["qualification_score"] >= 0.7 for lead in result["leads"])


@pytest.mark.asyncio
async def test_update_lead_status(test_session, test_data):
    """Test updating a lead's status."""
    manager = PaymentHandoffManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.update_lead_status(
        tenant_id=tenant_id,
        lead_id="lead-001",
        new_status="CONTACTED",
        notes="Customer engaged",
    )
    
    assert result["status"] == "success"
    assert result["lead"]["status"] == "CONTACTED"


@pytest.mark.asyncio
async def test_multi_tenant_isolation_leads(test_session, test_data):
    """Test that tenant 1 leads don't appear for tenant 2."""
    manager = PaymentHandoffManager(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Get leads for tenant 2
    result = await manager.get_leads(tenant_id=tenant_2_id)
    
    # Should be empty
    assert len(result["leads"]) == 0
    
    # Verify tenant 1 has leads
    result_t1 = await manager.get_leads(tenant_id=tenant_1_id)
    assert len(result_t1["leads"]) > 0


@pytest.mark.asyncio
async def test_cannot_access_other_tenant_lead(test_session, test_data):
    """Test that updating another tenant's lead fails."""
    manager = PaymentHandoffManager(test_session)
    tenant_2_id = test_data["tenant_2_id"]
    
    # Try to update tenant 1's lead as tenant 2
    result = await manager.update_lead_status(
        tenant_id=tenant_2_id,
        lead_id="lead-001",  # Belongs to tenant 1
        new_status="CONVERTED",
        notes="Unauthorized update",
    )
    
    # Should fail or return empty
    assert result["status"] == "error" or result.get("lead") is None
