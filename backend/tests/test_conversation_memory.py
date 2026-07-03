"""
Integration tests for ConversationMemory.

Tests:
- Conversation creation and retrieval
- Message addition with entity extraction
- Conversation closing and summarization
- Intent detection
- Multi-tenant isolation
"""

import pytest
from conversation_memory import ConversationMemory


@pytest.mark.asyncio
async def test_create_conversation(test_session, test_data):
    """Test creating a new conversation."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.create_conversation(
        tenant_id=tenant_id,
        call_sid="CA_NEW_12345",
        customer_phone="+1-555-6001",
    )
    
    assert result["status"] == "success"
    assert result["conversation"]["customer_phone"] == "+1-555-6001"
    assert result["conversation"]["status"] == "OPEN"


@pytest.mark.asyncio
async def test_add_message_to_conversation(test_session, test_data):
    """Test adding a message to an existing conversation."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    # Create conversation
    create_result = await manager.create_conversation(
        tenant_id=tenant_id,
        call_sid="CA_NEW_67890",
        customer_phone="+1-555-6002",
    )
    conversation_id = create_result["conversation"]["conversation_id"]
    
    # Add message
    result = await manager.add_message(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        role="customer",
        text="I would like to order a large pepperoni pizza",
        entities={"food": "pizza", "size": "large"},
    )
    
    assert result["status"] == "success"
    assert len(result["conversation"]["transcript"]) == 1


@pytest.mark.asyncio
async def test_get_conversation_context(test_session, test_data):
    """Test retrieving conversation context."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.get_conversation_context(
        tenant_id=tenant_id,
        conversation_id="conv-001",
    )
    
    assert result["status"] == "success"
    assert result["conversation"]["call_sid"] == "CA1234567890abcdef"
    assert len(result["conversation"]["transcript"]) == 3


@pytest.mark.asyncio
async def test_close_conversation(test_session, test_data):
    """Test closing a conversation."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.close_conversation(
        tenant_id=tenant_id,
        conversation_id="conv-001",
        outcome="ORDER_PLACED",
        transferred_to_human=False,
        duration_seconds=180,
    )
    
    assert result["status"] == "success"
    assert result["conversation"]["status"] == "CLOSED"


@pytest.mark.asyncio
async def test_get_recent_conversations(test_session, test_data):
    """Test retrieving recent conversations."""
    manager = ConversationMemory(test_session)
    tenant_id = test_data["tenant_1_id"]
    
    result = await manager.get_recent_conversations(
        tenant_id=tenant_id,
        limit=10,
    )
    
    assert result["status"] == "success"
    assert len(result["conversations"]) >= 1
    # Most recent should be first
    assert result["conversations"][0]["conversation_id"] == "conv-001"


@pytest.mark.asyncio
async def test_intent_detection_order(test_session, test_data):
    """Test intent detection for ORDER."""
    manager = ConversationMemory(test_session)
    
    intent = manager._detect_intent("I want to place an order for pizza")
    assert intent == "ORDER"


@pytest.mark.asyncio
async def test_intent_detection_reservation(test_session, test_data):
    """Test intent detection for RESERVATION."""
    manager = ConversationMemory(test_session)
    
    intent = manager._detect_intent("Can I make a reservation for tomorrow?")
    assert intent == "RESERVATION"


@pytest.mark.asyncio
async def test_multi_tenant_isolation_conversations(test_session, test_data):
    """Test that tenant 1 conversations don't appear for tenant 2."""
    manager = ConversationMemory(test_session)
    tenant_1_id = test_data["tenant_1_id"]
    tenant_2_id = test_data["tenant_2_id"]
    
    # Get recent conversations for tenant 2
    result = await manager.get_recent_conversations(
        tenant_id=tenant_2_id,
        limit=10,
    )
    
    # Should be empty
    assert len(result["conversations"]) == 0
    
    # Verify tenant 1 has conversations
    result_t1 = await manager.get_recent_conversations(
        tenant_id=tenant_1_id,
        limit=10,
    )
    assert len(result_t1["conversations"]) > 0


@pytest.mark.asyncio
async def test_cannot_access_other_tenant_conversation(test_session, test_data):
    """Test that accessing another tenant's conversation fails."""
    manager = ConversationMemory(test_session)
    tenant_2_id = test_data["tenant_2_id"]
    
    # Try to get tenant 1's conversation as tenant 2
    result = await manager.get_conversation_context(
        tenant_id=tenant_2_id,
        conversation_id="conv-001",  # Belongs to tenant 1
    )
    
    # Should fail or return empty
    assert result["status"] == "error" or result.get("conversation") is None
