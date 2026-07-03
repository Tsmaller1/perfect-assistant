"""
Integration tests for AppointmentManager.

Tests:
- Appointment creation and retrieval
- Availability checking with conflict detection
- Appointment cancellation
- Status updates
- Multi-tenant isolation
"""

import pytest
from datetime import datetime
from appointments import AppointmentManager


@pytest.mark.asyncio
async def test_book_appointment(test_session, test_data):
    """Test booking a new appointment."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.book_appointment(
        tenant_id=tenant_id,
        customer_name="Eve",
        customer_email="eve@example.com",
        customer_phone="+1-555-5001",
        scheduled_datetime="2026-07-15 14:00:00",
        service_type="Dine-In",
        duration_minutes=90,
        notes="Birthday party",
    )
    
    assert result["status"] == "success"
    assert result["appointment"]["customer_name"] == "Eve"
    assert result["appointment"]["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_check_availability_no_conflict(test_session, test_data):
    """Test availability checking when no conflicts exist."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Request 2-hour slot at 12pm (existing appointments are 2pm and 3pm)
    available = await manager.check_availability(
        tenant_id=tenant_id,
        date_str="2026-07-10",
        start_time="12:00",
        duration_minutes=120,
    )
    
    assert available is True


@pytest.mark.asyncio
async def test_check_availability_with_conflict(test_session, test_data):
    """Test availability checking detects conflicts."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Request 2-hour slot at 2pm (conflicts with 2pm appointment)
    available = await manager.check_availability(
        tenant_id=tenant_id,
        date_str="2026-07-10",
        start_time="14:00",
        duration_minutes=120,
    )
    
    assert available is False


@pytest.mark.asyncio
async def test_get_appointments(test_session, test_data):
    """Test retrieving appointments for a tenant."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    appointments = await manager.get_appointments(tenant_id=tenant_id)
    
    assert len(appointments) == 2
    assert all(appt["tenant_id"] == tenant_id for appt in appointments)


@pytest.mark.asyncio
async def test_get_appointments_by_status(test_session, test_data):
    """Test retrieving appointments filtered by status."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    appointments = await manager.get_appointments(
        tenant_id=tenant_id,
        status="CONFIRMED"
    )
    
    assert len(appointments) == 2
    assert all(appt["status"] == "CONFIRMED" for appt in appointments)


@pytest.mark.asyncio
async def test_cancel_appointment(test_session, test_data):
    """Test cancelling an appointment."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.cancel_appointment(
        tenant_id=tenant_id,
        appointment_id="appt-001",
        reason="Customer requested cancellation",
    )
    
    assert result["status"] == "success"
    assert result["appointment"]["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_update_appointment_status(test_session, test_data):
    """Test updating appointment status."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.update_appointment_status(
        tenant_id=tenant_id,
        appointment_id="appt-001",
        new_status="NO_SHOW",
    )
    
    assert result["status"] == "success"
    assert result["appointment"]["status"] == "NO_SHOW"


@pytest.mark.asyncio
async def test_get_daily_schedule(test_session, test_data):
    """Test retrieving daily schedule for a date."""
    manager = AppointmentManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    schedule = await manager.get_daily_schedule(
        tenant_id=tenant_id,
        date_str="2026-07-10",
    )
    
    assert len(schedule) == 2  # Two appointments on this date
    assert schedule[0]["scheduled_datetime"].startswith("2026-07-10")


@pytest.mark.asyncio
async def test_multi_tenant_isolation(test_session, test_data):
    """Test that tenant 1 appointments don't appear for tenant 2."""
    manager = AppointmentManager(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Get appointments for tenant 2
    appointments = await manager.get_appointments(tenant_id=tenant_2_id)
    
    # Should be empty (no appointments for tenant 2)
    assert len(appointments) == 0
    
    # Verify tenant 1 still has appointments
    appointments_t1 = await manager.get_appointments(tenant_id=tenant_1_id)
    assert len(appointments_t1) == 2


@pytest.mark.asyncio
async def test_cannot_access_other_tenant_appointment(test_session, test_data):
    """Test that cancelling another tenant's appointment fails."""
    manager = AppointmentManager(test_session)
    tenant_2_id = test_data["tenant_2_id"]
    
    # Try to cancel tenant 1's appointment as tenant 2
    result = await manager.cancel_appointment(
        tenant_id=tenant_2_id,
        appointment_id="appt-001",  # Belongs to tenant 1
        reason="Unauthorized cancel",
    )
    
    # Should fail because appointment doesn't exist for tenant 2
    assert result["status"] == "error" or result.get("appointment") is None
