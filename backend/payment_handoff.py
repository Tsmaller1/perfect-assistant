"""
Payment Handoff System
Transfers calls to humans when payment is needed, creates lead records
Uses SQLAlchemy ORM with Supabase PostgreSQL
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client as TwilioClient
from models import Lead

logger = logging.getLogger(__name__)


class PaymentHandoffManager:
    """Manages payment handoff to human representatives via database."""

    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: AsyncSession from SQLAlchemy
        """
        self.session = session
        # Initialize Twilio client (from env in production)
        self.twilio_client = None

    async def initiate_payment_handoff(
        self,
        tenant_id: str,
        call_sid: str,
        owner_phone: str,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
        order_value: Optional[float] = None,
        order_items: Optional[list] = None,
        notes: str = "",
    ) -> dict:
        """
        Initiate payment handoff for a customer call.
        Creates a lead record in database and facilitates transfer to human.

        Args:
            tenant_id: Business tenant ID
            call_sid: Twilio call SID
            owner_phone: Business owner/rep phone number
            customer_name: Customer name
            customer_phone: Customer phone
            customer_email: Customer email
            order_value: Value of potential order
            order_items: Items ordered
            notes: Additional notes

        Returns:
            {
                "status": "success|error",
                "lead_id": "...",
                "transfer_initiated": True/False
            }
        """
        try:
            # Create lead object
            lead_id = str(uuid.uuid4())
            lead = Lead(
                lead_id=lead_id,
                tenant_id=tenant_id,
                call_sid=call_sid,
                customer_name=customer_name or "Unknown",
                customer_phone=customer_phone,
                customer_email=customer_email,
                order_value=order_value,
                order_items=order_items or [],
                status="PAYMENT_PENDING",
                payment_status="PENDING",
                qualification_score=self._calculate_qualification_score(order_value),
                notes=notes,
            )

            # Save to database
            self.session.add(lead)
            await self.session.commit()

            logger.info(
                f"Payment handoff initiated | tenant={tenant_id} | lead_id={lead_id} | call_sid={call_sid}"
            )

            return {
                "status": "success",
                "lead_id": lead_id,
                "transfer_initiated": True,
                "message": "Transferring to payment representative...",
            }

        except Exception as e:
            logger.error(f"Payment handoff error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e), "transfer_initiated": False}

    async def complete_payment_transfer(
        self,
        call_sid: str,
        payment_status: str = "PENDING",
        payment_method: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> dict:
        """
        Mark payment transfer as complete in database.

        Args:
            call_sid: Twilio call SID
            payment_status: PENDING, AUTHORIZED, COMPLETED, FAILED
            payment_method: Card type or method used
            amount: Amount charged

        Returns:
            Status of completion
        """
        try:
            # Query lead by call_sid
            stmt = select(Lead).where(Lead.call_sid == call_sid)
            result = await self.session.execute(stmt)
            lead = result.scalar_one_or_none()

            if not lead:
                return {"status": "error", "error": "Lead not found"}

            # Update lead status
            lead.payment_status = payment_status
            lead.payment_method = payment_method
            lead.amount = amount
            
            if payment_status == "COMPLETED":
                lead.status = "CONVERTED"
            else:
                lead.status = payment_status

            await self.session.commit()

            logger.info(
                f"Payment transfer completed | call_sid={call_sid} | status={payment_status}"
            )

            return {
                "status": "success",
                "lead_id": lead.lead_id,
                "payment_status": payment_status,
            }

        except Exception as e:
            logger.error(f"Complete transfer error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def get_leads(self, tenant_id: str, status: Optional[str] = None) -> dict:
        """Get all leads for a tenant from database."""
        try:
            query = select(Lead).where(Lead.tenant_id == tenant_id)

            if status:
                query = query.where(Lead.status == status)
            
            # Order by qualification score (highest first)
            query = query.order_by(Lead.qualification_score.desc())
            
            result = await self.session.execute(query)
            leads = result.scalars().all()

            return {
                "status": "success",
                "count": len(leads),
                "leads": [
                    {
                        "lead_id": lead.lead_id,
                        "customer_name": lead.customer_name,
                        "customer_phone": lead.customer_phone,
                        "customer_email": lead.customer_email,
                        "order_value": lead.order_value,
                        "status": lead.status,
                        "payment_status": lead.payment_status,
                        "qualification_score": lead.qualification_score,
                        "created_at": lead.created_at.isoformat(),
                    }
                    for lead in leads
                ],
            }

        except Exception as e:
            logger.error(f"Get leads error: {e}")
            return {"status": "error", "error": str(e)}

    async def update_lead_status(
        self, tenant_id: str, lead_id: str, new_status: str, notes: str = ""
    ) -> dict:
        """Update lead status in database."""
        try:
            # Query lead from database
            stmt = select(Lead).where(
                (Lead.tenant_id == tenant_id) &
                (Lead.lead_id == lead_id)
            )
            result = await self.session.execute(stmt)
            lead = result.scalar_one_or_none()

            if not lead:
                return {"status": "error", "error": "Lead not found"}

            lead.status = new_status
            if notes:
                existing_notes = lead.notes or ""
                lead.notes = f"{existing_notes}\n[{datetime.now(timezone.utc).isoformat()}] {notes}".strip()

            await self.session.commit()

            logger.info(f"Lead status updated | lead_id={lead_id} | status={new_status}")

            return {
                "status": "success",
                "lead": {
                    "lead_id": lead.lead_id,
                    "customer_name": lead.customer_name,
                    "customer_phone": lead.customer_phone,
                    "customer_email": lead.customer_email,
                    "status": lead.status,
                    "created_at": lead.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Update lead error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    def _calculate_qualification_score(self, order_value: Optional[float]) -> float:
        """
        Calculate lead qualification score (0-1).
        Based on order value and other factors.
        """
        score = 0.5  # Base score

        if order_value:
            # Higher order value = higher qualification
            if order_value > 100:
                score += 0.3
            elif order_value > 50:
                score += 0.2
            elif order_value > 0:
                score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    async def get_qualified_leads(
        self, tenant_id: str, min_score: float = 0.6
    ) -> dict:
        """Get only high-quality leads from database."""
        try:
            query = select(Lead).where(
                (Lead.tenant_id == tenant_id) &
                (Lead.qualification_score >= min_score) &
                (Lead.status.in_(["PAYMENT_PENDING", "AUTHORIZED"]))
            ).order_by(Lead.qualification_score.desc())
            
            result = await self.session.execute(query)
            leads = result.scalars().all()

            return {
                "status": "success",
                "count": len(leads),
                "qualified_leads": [
                    {
                        "lead_id": lead.lead_id,
                        "customer_name": lead.customer_name,
                        "customer_phone": lead.customer_phone,
                        "customer_email": lead.customer_email,
                        "order_value": lead.order_value,
                        "qualification_score": lead.qualification_score,
                        "status": lead.status,
                        "created_at": lead.created_at.isoformat(),
                    }
                    for lead in leads
                ],
            }

        except Exception as e:
            logger.error(f"Get qualified leads error: {e}")
            return {"status": "error", "error": str(e)}
