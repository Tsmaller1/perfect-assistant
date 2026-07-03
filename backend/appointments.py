"""
Appointments/Reservations Management
Handles scheduling, availability checking, and booking
Uses SQLAlchemy ORM with Supabase PostgreSQL
"""

import logging
from datetime import datetime, timedelta, timezone, date
from typing import Optional
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Appointment

logger = logging.getLogger(__name__)


class AppointmentManager:
    """Manages business appointments and availability via database."""

    def __init__(self, session: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            session: AsyncSession from SQLAlchemy
        """
        self.session = session

    async def check_availability(
        self,
        tenant_id: str,
        date_str: str,
        start_time: str = "09:00",
        duration_minutes: int = 30,
    ) -> dict:
        """
        Check if a time slot is available by querying database.

        Args:
            tenant_id: Business tenant ID
            date_str: Date in YYYY-MM-DD format
            start_time: Time in HH:MM format
            duration_minutes: Duration of appointment

        Returns:
            {
                "available": True/False,
                "conflicts": [...]
            }
        """
        try:
            # Parse datetime
            dt_str = f"{date_str} {start_time}"
            requested_start = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            requested_end = requested_start + timedelta(minutes=duration_minutes)

            # Query database for tenant's appointments (exclude CANCELLED/COMPLETED)
            stmt = select(Appointment).where(
                (Appointment.tenant_id == tenant_id) &
                (Appointment.status.in_(["BOOKED", "IN_PROGRESS"]))
            )
            result = await self.session.execute(stmt)
            appointments = result.scalars().all()

            # Check for conflicts
            conflicts = []
            for apt in appointments:
                apt_start = apt.scheduled_datetime
                apt_end = apt_start + timedelta(minutes=apt.duration_minutes)

                # Check for overlap
                if requested_start < apt_end and requested_end > apt_start:
                    conflicts.append(
                        {
                            "appointment_id": apt.appointment_id,
                            "customer_name": apt.customer_name,
                            "time": apt.scheduled_datetime.isoformat(),
                        }
                    )

            available = len(conflicts) == 0

            return {
                "available": available,
                "date": date_str,
                "start_time": start_time,
                "conflicts": conflicts,
            }

        except Exception as e:
            logger.error(f"Availability check error: {e}")
            return {"available": False, "error": str(e)}

    async def book_appointment(
        self,
        tenant_id: str,
        customer_name: str,
        customer_email: Optional[str],
        customer_phone: Optional[str],
        scheduled_datetime: str,
        service_type: str = "General",
        duration_minutes: int = 30,
        notes: str = "",
    ) -> dict:
        """
        Book a new appointment in database.

        Args:
            tenant_id: Business tenant ID
            customer_name: Customer name
            customer_email: Customer email
            customer_phone: Customer phone
            scheduled_datetime: ISO format datetime string
            service_type: Type of service
            duration_minutes: Duration
            notes: Additional notes

        Returns:
            {
                "status": "success|error",
                "appointment_id": "...",
                "appointment": {...}
            }
        """
        try:
            # Check availability
            dt = datetime.fromisoformat(scheduled_datetime)
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")

            availability = await self.check_availability(
                tenant_id, date_str, time_str, duration_minutes
            )

            if not availability["available"]:
                return {
                    "status": "error",
                    "error": f"Time slot not available. Conflicts: {availability['conflicts']}",
                }

            # Create appointment object
            appointment_id = str(uuid.uuid4())
            appointment = Appointment(
                appointment_id=appointment_id,
                tenant_id=tenant_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                scheduled_datetime=datetime.fromisoformat(scheduled_datetime),
                service_type=service_type,
                duration_minutes=duration_minutes,
                status="BOOKED",
                notes=notes,
            )

            # Save to database
            self.session.add(appointment)
            await self.session.commit()

            logger.info(
                f"Appointment booked | tenant={tenant_id} | appointment_id={appointment_id}"
            )

            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment": {
                    "appointment_id": appointment.appointment_id,
                    "tenant_id": appointment.tenant_id,
                    "customer_name": appointment.customer_name,
                    "customer_email": appointment.customer_email,
                    "customer_phone": appointment.customer_phone,
                    "scheduled_datetime": appointment.scheduled_datetime.isoformat(),
                    "service_type": appointment.service_type,
                    "duration_minutes": appointment.duration_minutes,
                    "status": appointment.status,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Booking error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def get_appointments(
        self, tenant_id: str, status: Optional[str] = None
    ) -> dict:
        """Get all appointments for a tenant from database."""
        try:
            query = select(Appointment).where(Appointment.tenant_id == tenant_id)
            
            if status:
                query = query.where(Appointment.status == status)
            
            result = await self.session.execute(query)
            appointments = result.scalars().all()

            return {
                "status": "success",
                "count": len(appointments),
                "appointments": [
                    {
                        "appointment_id": apt.appointment_id,
                        "tenant_id": apt.tenant_id,
                        "customer_name": apt.customer_name,
                        "customer_email": apt.customer_email,
                        "customer_phone": apt.customer_phone,
                        "scheduled_datetime": apt.scheduled_datetime.isoformat(),
                        "service_type": apt.service_type,
                        "duration_minutes": apt.duration_minutes,
                        "status": apt.status,
                        "notes": apt.notes,
                        "created_at": apt.created_at.isoformat(),
                    }
                    for apt in appointments
                ],
            }

        except Exception as e:
            logger.error(f"Get appointments error: {e}")
            return {"status": "error", "error": str(e)}

    async def cancel_appointment(
        self, tenant_id: str, appointment_id: str, reason: str = ""
    ) -> dict:
        """Cancel an appointment in database."""
        try:
            stmt = select(Appointment).where(
                (Appointment.tenant_id == tenant_id) &
                (Appointment.appointment_id == appointment_id)
            )
            result = await self.session.execute(stmt)
            appointment = result.scalar_one_or_none()

            if not appointment:
                return {"status": "error", "error": "Appointment not found"}

            appointment.status = "CANCELLED"
            appointment.notes = f"{appointment.notes}\n\nCancellation reason: {reason}" if appointment.notes else f"Cancellation reason: {reason}"
            
            await self.session.commit()

            logger.info(
                f"Appointment cancelled | tenant={tenant_id} | appointment_id={appointment_id}"
            )

            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment": {
                    "appointment_id": appointment.appointment_id,
                    "tenant_id": appointment.tenant_id,
                    "customer_name": appointment.customer_name,
                    "customer_email": appointment.customer_email,
                    "customer_phone": appointment.customer_phone,
                    "scheduled_datetime": appointment.scheduled_datetime.isoformat(),
                    "service_type": appointment.service_type,
                    "duration_minutes": appointment.duration_minutes,
                    "status": appointment.status,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def update_appointment_status(
        self, tenant_id: str, appointment_id: str, new_status: str
    ) -> dict:
        """Update appointment status in database."""
        try:
            stmt = select(Appointment).where(
                (Appointment.tenant_id == tenant_id) &
                (Appointment.appointment_id == appointment_id)
            )
            result = await self.session.execute(stmt)
            appointment = result.scalar_one_or_none()

            if not appointment:
                return {"status": "error", "error": "Appointment not found"}

            appointment.status = new_status
            await self.session.commit()

            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment": {
                    "appointment_id": appointment.appointment_id,
                    "tenant_id": appointment.tenant_id,
                    "customer_name": appointment.customer_name,
                    "customer_email": appointment.customer_email,
                    "customer_phone": appointment.customer_phone,
                    "scheduled_datetime": appointment.scheduled_datetime.isoformat(),
                    "service_type": appointment.service_type,
                    "duration_minutes": appointment.duration_minutes,
                    "status": appointment.status,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Update status error: {e}")
            await self.session.rollback()
            return {"status": "error", "error": str(e)}

    async def get_daily_schedule(self, tenant_id: str, date_str: str) -> dict:
        """Get all appointments for a specific day from database."""
        try:
            # Parse date
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            next_date = target_date + timedelta(days=1)

            # Query for appointments on that day (excluding CANCELLED)
            stmt = select(Appointment).where(
                (Appointment.tenant_id == tenant_id) &
                (func.date(Appointment.scheduled_datetime) == target_date) &
                (Appointment.status != "CANCELLED")
            ).order_by(Appointment.scheduled_datetime)
            
            result = await self.session.execute(stmt)
            appointments = result.scalars().all()

            return {
                "status": "success",
                "date": date_str,
                "count": len(appointments),
                "appointments": [
                    {
                        "appointment_id": apt.appointment_id,
                        "tenant_id": apt.tenant_id,
                        "customer_name": apt.customer_name,
                        "customer_email": apt.customer_email,
                        "customer_phone": apt.customer_phone,
                        "scheduled_datetime": apt.scheduled_datetime.isoformat(),
                        "service_type": apt.service_type,
                        "duration_minutes": apt.duration_minutes,
                        "status": apt.status,
                        "notes": apt.notes,
                        "created_at": apt.created_at.isoformat(),
                    }
                    for apt in appointments
                ],
            }

        except Exception as e:
            logger.error(f"Daily schedule error: {e}")
            return {"status": "error", "error": str(e)}
