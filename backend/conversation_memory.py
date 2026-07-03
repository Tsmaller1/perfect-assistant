"""
Conversation Memory & Context Management
Stores conversations, extracts entities, builds AI context
Uses SQLAlchemy ORM with Supabase PostgreSQL
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Conversation

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation storage and context building via database."""

    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: AsyncSession from SQLAlchemy
        """
        self.session = session

    async def create_conversation(
        self,
        tenant_id: str,
        call_sid: str,
        customer_phone: Optional[str] = None,
    ) -> dict:
        """
        Create a new conversation record in database.

        Args:
            tenant_id: Business tenant ID
            call_sid: Twilio call SID
            customer_phone: Customer phone number

        Returns:
            {
                "status": "success",
                "conversation_id": "..."
            }
        """
        try:
            conversation_id = str(uuid.uuid4())

            conversation = Conversation(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                call_sid=call_sid,
                customer_phone=customer_phone,
                transcript=[],  # Initialize as empty array
                entities={},    # Initialize as empty object
                intent=None,
                summary=None,
                outcome=None,
                transferred_to_human=False,
                duration_seconds=0,
            )

            # Save to database
            self.session.add(conversation)
            await self.session.commit()

            logger.info(
                f"Conversation created | tenant={tenant_id} | conversation_id={conversation_id}"
            )

            return {"status": "success", "conversation_id": conversation_id}

        except Exception as e:
            logger.error(f"Create conversation error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def add_message(
        self,
        tenant_id: str,
        conversation_id: str,
        role: str,
        text: str,
        entities: Optional[dict] = None,
    ) -> dict:
        """
        Add a message to a conversation in database.

        Args:
            tenant_id: Business tenant ID
            conversation_id: Conversation ID
            role: "user" or "ai"
            text: Message text
            entities: Extracted entities from message

        Returns:
            Status of addition
        """
        try:
            # Query conversation from database
            stmt = select(Conversation).where(
                (Conversation.tenant_id == tenant_id) &
                (Conversation.conversation_id == conversation_id)
            )
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                return {"status": "error", "error": "Conversation not found"}

            # Add message to transcript array
            message = {
                "role": role,
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            if conversation.transcript is None:
                conversation.transcript = []
            conversation.transcript.append(message)

            # Update entities if provided
            if entities:
                if conversation.entities is None:
                    conversation.entities = {}
                conversation.entities.update(entities)

            # Detect intent from user message
            if role == "user":
                conversation.intent = self._detect_intent(text)

            await self.session.commit()

            return {"status": "success", "transcript_length": len(conversation.transcript)}

        except Exception as e:
            logger.error(f"Add message error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def close_conversation(
        self,
        tenant_id: str,
        conversation_id: str,
        outcome: str = "COMPLETED",
        transferred_to_human: bool = False,
        duration_seconds: int = 0,
    ) -> dict:
        """
        Close a conversation and finalize context in database.

        Args:
            tenant_id: Business tenant ID
            conversation_id: Conversation ID
            outcome: COMPLETED, TRANSFERRED, FAILED, etc.
            transferred_to_human: Whether transferred before close
            duration_seconds: Call duration

        Returns:
            Final conversation record
        """
        try:
            # Query conversation from database
            stmt = select(Conversation).where(
                (Conversation.tenant_id == tenant_id) &
                (Conversation.conversation_id == conversation_id)
            )
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                return {"status": "error", "error": "Conversation not found"}

            # Finalize conversation
            conversation.outcome = outcome
            conversation.transferred_to_human = transferred_to_human
            conversation.duration_seconds = duration_seconds
            conversation.summary = self._build_transcript_text(conversation.transcript)

            await self.session.commit()

            logger.info(
                f"Conversation closed | conversation_id={conversation_id} | outcome={outcome}"
            )

            return {
                "status": "success",
                "conversation": {
                    "conversation_id": conversation.conversation_id,
                    "tenant_id": conversation.tenant_id,
                    "call_sid": conversation.call_sid,
                    "customer_phone": conversation.customer_phone,
                    "intent": conversation.intent,
                    "outcome": conversation.outcome,
                    "transferred_to_human": conversation.transferred_to_human,
                    "duration_seconds": conversation.duration_seconds,
                    "transcript_length": len(conversation.transcript) if conversation.transcript else 0,
                    "created_at": conversation.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Close conversation error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def get_conversation_context(
        self, tenant_id: str, conversation_id: str
    ) -> dict:
        """
        Get conversation context for AI to review from database.

        Returns:
            {
                "entities": {...extracted data...},
                "transcript": [...],
                "intent": "...",
                "summary": "..."
            }
        """
        try:
            # Query conversation from database
            stmt = select(Conversation).where(
                (Conversation.tenant_id == tenant_id) &
                (Conversation.conversation_id == conversation_id)
            )
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                return {"status": "error", "error": "Conversation not found"}

            return {
                "status": "success",
                "context": {
                    "conversation_id": conversation_id,
                    "entities": conversation.entities or {},
                    "transcript": conversation.transcript or [],
                    "intent": conversation.intent,
                    "outcome": conversation.outcome,
                    "summary": self._summarize_conversation(conversation),
                },
            }

        except Exception as e:
            logger.error(f"Get context error: {e}")
            return {"status": "error", "error": str(e)}

    async def get_recent_conversations(
        self, tenant_id: str, limit: int = 50
    ) -> dict:
        """Get recent conversations for a tenant from database."""
        try:
            stmt = select(Conversation).where(
                Conversation.tenant_id == tenant_id
            ).order_by(Conversation.created_at.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            conversations = result.scalars().all()

            return {
                "status": "success",
                "count": len(conversations),
                "conversations": [
                    {
                        "conversation_id": conv.conversation_id,
                        "call_sid": conv.call_sid,
                        "customer_phone": conv.customer_phone,
                        "intent": conv.intent,
                        "outcome": conv.outcome,
                        "transferred_to_human": conv.transferred_to_human,
                        "duration_seconds": conv.duration_seconds,
                        "created_at": conv.created_at.isoformat(),
                    }
                    for conv in conversations
                ],
            }

        except Exception as e:
            logger.error(f"Get recent conversations error: {e}")
            return {"status": "error", "error": str(e)}

    def _detect_intent(self, text: str) -> str:
        """Detect user intent from message."""
        text_lower = text.lower()

        intent_keywords = {
            "BOOK_APPOINTMENT": ["book", "schedule", "appointment", "reserve", "availability"],
            "ASK_QUESTION": ["what", "how", "when", "where", "who", "why", "tell", "explain"],
            "PLACE_ORDER": ["order", "buy", "purchase", "want", "like", "get"],
            "CHECK_PRICE": ["price", "cost", "how much", "afford", "expensive"],
            "COMPLAINT": ["problem", "issue", "broken", "not work", "angry", "mad"],
            "CANCEL": ["cancel", "refund", "return", "stop"],
        }

        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return intent

        return "GENERAL"

    def _build_transcript_text(self, transcript: Optional[list]) -> str:
        """Build readable transcript from messages."""
        if not transcript:
            return ""
        
        lines = []
        for msg in transcript:
            role = "User" if msg.get("role") == "user" else "AI"
            lines.append(f"{role}: {msg.get('text', '')}")

        return "\n".join(lines)

    def _summarize_conversation(self, conversation: Conversation) -> str:
        """Generate brief summary of conversation from ORM object."""
        parts = []

        if conversation.intent:
            parts.append(f"Intent: {conversation.intent}")

        if conversation.entities:
            parts.append(f"Entities: {json.dumps(conversation.entities)}")

        if conversation.outcome:
            parts.append(f"Outcome: {conversation.outcome}")

        if conversation.transferred_to_human:
            parts.append("Transferred to human agent")

        return " | ".join(parts) if parts else "No summary available"

    async def extract_entities_from_transcript(
        self, conversation_id: str, transcript: list[dict]
    ) -> dict:
        """
        Extract entities (names, emails, dates, etc.) from transcript.

        This is a simplified implementation. In production,
        use NER (Named Entity Recognition) or NLP for better accuracy.
        """
        import re

        entities = {}

        full_text = " ".join([msg["text"] for msg in transcript])

        # Simple regex-based extraction
        name_patterns = [
            r"(?:my name is|i'm|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                entities["name"] = match.group(1)
                break

        # Email
        email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", full_text)
        if email_match:
            entities["email"] = email_match.group(1)

        # Phone
        phone_match = re.search(
            r"(\+?1?)[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})", full_text
        )
        if phone_match:
            entities["phone"] = phone_match.group(0)

        # Date patterns
        date_match = re.search(
            r"((?:mon|tue|wed|thu|fri|sat|sun|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w\s]*\d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)",
            full_text,
            re.IGNORECASE,
        )
        if date_match:
            entities["date"] = date_match.group(1)

        return entities


# Global instance
conversation_memory = ConversationMemory()
