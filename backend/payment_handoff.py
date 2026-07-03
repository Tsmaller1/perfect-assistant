"""
Payment Handoff System
Transfers calls to humans when payment is needed, creates lead records
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)

# In-memory storage (replace with DB in production)
LEADS = {}  # {tenant_id: [leads]}
PAYMENT_TRANSFERS = {}  # {call_sid: transfer_info}


class PaymentHandoffManager:
    """Manages payment handoff to human representatives."""

    def __init__(self):
        self.leads = LEADS
        self.transfers = PAYMENT_TRANSFERS
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
        Creates a lead record and facilitates transfer to human.

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
            # Create lead record
            lead_id = str(uuid.uuid4())
            lead = {
                "lead_id": lead_id,
                "tenant_id": tenant_id,
                "customer_name": customer_name or "Unknown",
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "order_value": order_value,
                "order_items": order_items or [],
                "notes": notes,
                "qualification_score": self._calculate_qualification_score(order_value),
                "status": "PAYMENT_PENDING",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Store lead
            if tenant_id not in self.leads:
                self.leads[tenant_id] = []

            self.leads[tenant_id].append(lead)

            # Record transfer
            transfer = {
                "call_sid": call_sid,
                "lead_id": lead_id,
                "tenant_id": tenant_id,
                "initiated_at": datetime.now(timezone.utc).isoformat(),
                "owner_phone": owner_phone,
                "status": "INITIATED",
            }

            self.transfers[call_sid] = transfer

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
            return {"status": "error", "error": str(e), "transfer_initiated": False}

    async def complete_payment_transfer(
        self,
        call_sid: str,
        payment_status: str = "PENDING",
        payment_method: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> dict:
        """
        Mark payment transfer as complete.

        Args:
            call_sid: Twilio call SID
            payment_status: PENDING, AUTHORIZED, COMPLETED, FAILED
            payment_method: Card type or method used
            amount: Amount charged

        Returns:
            Status of completion
        """
        try:
            transfer = self.transfers.get(call_sid)

            if not transfer:
                return {"status": "error", "error": "Transfer not found"}

            lead_id = transfer["lead_id"]
            tenant_id = transfer["tenant_id"]

            # Update transfer
            transfer["status"] = "COMPLETED"
            transfer["completed_at"] = datetime.now(timezone.utc).isoformat()
            transfer["payment_status"] = payment_status
            transfer["amount"] = amount

            # Update lead status
            leads = self.leads.get(tenant_id, [])
            for lead in leads:
                if lead["lead_id"] == lead_id:
                    lead["status"] = payment_status
                    if payment_status == "COMPLETED":
                        lead["status"] = "CONVERTED"
                    lead["payment_method"] = payment_method
                    lead["amount_paid"] = amount
                    lead["updated_at"] = datetime.now(timezone.utc).isoformat()
                    break

            logger.info(
                f"Payment transfer completed | call_sid={call_sid} | status={payment_status}"
            )

            return {
                "status": "success",
                "lead_id": lead_id,
                "payment_status": payment_status,
            }

        except Exception as e:
            logger.error(f"Complete transfer error: {e}")
            return {"status": "error", "error": str(e)}

    async def get_leads(self, tenant_id: str, status: Optional[str] = None) -> dict:
        """Get all leads for a tenant."""
        try:
            leads = self.leads.get(tenant_id, [])

            if status:
                leads = [lead for lead in leads if lead["status"] == status]

            # Sort by qualification score (highest first)
            leads.sort(key=lambda x: x.get("qualification_score", 0), reverse=True)

            return {
                "status": "success",
                "count": len(leads),
                "leads": leads,
            }

        except Exception as e:
            logger.error(f"Get leads error: {e}")
            return {"status": "error", "error": str(e)}

    async def update_lead_status(
        self, tenant_id: str, lead_id: str, new_status: str, notes: str = ""
    ) -> dict:
        """Update lead status."""
        try:
            leads = self.leads.get(tenant_id, [])

            lead = None
            for l in leads:
                if l["lead_id"] == lead_id:
                    lead = l
                    break

            if not lead:
                return {"status": "error", "error": "Lead not found"}

            lead["status"] = new_status
            if notes:
                lead["notes"] = (lead.get("notes", "") + f"\n[{datetime.now().isoformat()}] {notes}").strip()
            lead["updated_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Lead status updated | lead_id={lead_id} | status={new_status}")

            return {"status": "success", "lead": lead}

        except Exception as e:
            logger.error(f"Update lead error: {e}")
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
        """Get only high-quality leads."""
        try:
            leads = self.leads.get(tenant_id, [])

            qualified = [
                lead
                for lead in leads
                if lead.get("qualification_score", 0) >= min_score
                and lead["status"] in ["PAYMENT_PENDING", "AUTHORIZED"]
            ]

            # Sort by score
            qualified.sort(
                key=lambda x: x.get("qualification_score", 0), reverse=True
            )

            return {
                "status": "success",
                "count": len(qualified),
                "qualified_leads": qualified,
            }

        except Exception as e:
            logger.error(f"Get qualified leads error: {e}")
            return {"status": "error", "error": str(e)}


# Global instance
payment_handoff = PaymentHandoffManager()
