"""
Integration tests for ActionQueueManager.

Tests:
- Action creation and broadcasting
- Action status updates
- Recent actions retrieval
- Action types (ORDER, APPOINTMENT, LEAD, RESERVATION)
- WebSocket connection management (mocked)
- Multi-tenant isolation
"""

import pytest
from action_queue import ActionQueueManager, ActionType, ActionStatus


@pytest.mark.asyncio
async def test_broadcast_new_action(test_session, test_data):
    """Test broadcasting a new action."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.ORDER,
        customer_info={"name": "Jack", "phone": "+1-555-8001"},
        action_data={"items": [{"name": "Burger", "qty": 2}], "total": 25.00},
    )
    
    assert result["status"] == "success"
    assert result["action"]["action_type"] == "ORDER"
    assert result["action"]["status"] == "NEW"
    assert result["action"]["customer_info"]["name"] == "Jack"


@pytest.mark.asyncio
async def test_broadcast_appointment_action(test_session, test_data):
    """Test broadcasting an APPOINTMENT action."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.APPOINTMENT,
        customer_info={"name": "Karen", "phone": "+1-555-8002"},
        action_data={"datetime": "2026-07-20 10:00", "service": "Consultation"},
    )
    
    assert result["action"]["action_type"] == "APPOINTMENT"


@pytest.mark.asyncio
async def test_broadcast_lead_action(test_session, test_data):
    """Test broadcasting a LEAD action."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.LEAD,
        customer_info={"name": "Liam", "phone": "+1-555-8003"},
        action_data={"value": 500.00, "source": "phone"},
    )
    
    assert result["action"]["action_type"] == "LEAD"


@pytest.mark.asyncio
async def test_update_action_status(test_session, test_data):
    """Test updating an action's status."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Broadcast an action first
    create_result = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.ORDER,
        customer_info={"name": "Maya", "phone": "+1-555-8004"},
        action_data={"items": []},
    )
    action_id = create_result["action"]["action_id"]
    
    # Update its status
    result = await manager.update_action_status(
        tenant_id=tenant_id,
        action_id=action_id,
        new_status=ActionStatus.IN_PROGRESS,
        notes="Kitchen preparing",
    )
    
    assert result["status"] == "success"
    assert result["action"]["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_update_action_to_completed(test_session, test_data):
    """Test updating an action to COMPLETED status."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Get existing action and update it
    result = await manager.update_action_status(
        tenant_id=tenant_id,
        action_id="action-001",
        new_status=ActionStatus.COMPLETED,
        notes="Ready for pickup",
    )
    
    assert result["action"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_get_recent_actions(test_session, test_data):
    """Test retrieving recent actions for a tenant."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.get_recent_actions(
        tenant_id=tenant_id,
        limit=10,
    )
    
    assert result["status"] == "success"
    assert len(result["actions"]) >= 1
    # Should be ordered by most recent first
    assert all(action["tenant_id"] == tenant_id for action in result["actions"])


@pytest.mark.asyncio
async def test_get_recent_actions_limit(test_session, test_data):
    """Test that limit parameter is respected."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Create multiple actions
    for i in range(5):
        await manager.broadcast_new_action(
            tenant_id=tenant_id,
            action_type=ActionType.ORDER,
            customer_info={"name": f"Customer{i}"},
            action_data={},
        )
    
    # Request only 3
    result = await manager.get_recent_actions(
        tenant_id=tenant_id,
        limit=3,
    )
    
    # Should not exceed limit
    assert len(result["actions"]) <= 3


@pytest.mark.asyncio
async def test_multi_tenant_isolation_actions(test_session, test_data):
    """Test that tenant 1 actions don't appear for tenant 2."""
    manager = ActionQueueManager(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Get actions for tenant 2
    result = await manager.get_recent_actions(
        tenant_id=tenant_2_id,
        limit=10,
    )
    
    # Should be empty
    assert len(result["actions"]) == 0
    
    # Verify tenant 1 has actions
    result_t1 = await manager.get_recent_actions(
        tenant_id=tenant_1_id,
        limit=10,
    )
    assert len(result_t1["actions"]) > 0


@pytest.mark.asyncio
async def test_cannot_access_other_tenant_action(test_session, test_data):
    """Test that updating another tenant's action fails."""
    manager = ActionQueueManager(test_session)
    tenant_2_id = test_data["tenant_2_id"]
    
    # Try to update tenant 1's action as tenant 2
    result = await manager.update_action_status(
        tenant_id=tenant_2_id,
        action_id="action-001",  # Belongs to tenant 1
        new_status=ActionStatus.COMPLETED,
        notes="Unauthorized update",
    )
    
    # Should fail or return empty
    assert result["status"] == "error" or result.get("action") is None


@pytest.mark.asyncio
async def test_action_persists_to_database(test_session, test_data):
    """Test that actions are persisted to database."""
    manager = ActionQueueManager(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Broadcast an action
    result = await manager.broadcast_new_action(
        tenant_id=tenant_id,
        action_type=ActionType.RESERVATION,
        customer_info={"name": "Noah"},
        action_data={"table": 5},
    )
    action_id = result["action"]["action_id"]
    
    # Retrieve it again
    retrieved = await manager.get_recent_actions(
        tenant_id=tenant_id,
        limit=100,
    )
    
    # Should find it
    found = any(a["action_id"] == action_id for a in retrieved["actions"])
    assert found is True
