"""
Appointments/Reservations Management
Handles scheduling, availability checking, and booking
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


# In-memory storage (replace with DB in production)
APPOINTMENTS = {}  # {tenant_id: [appointments]}
BUSINESS_HOURS = {}  # {tenant_id: hours_config}


class AppointmentManager:
    """Manages business appointments and availability."""

    def __init__(self):
        self.appointments = APPOINTMENTS
        self.business_hours = BUSINESS_HOURS

    async def check_availability(
        self,
        tenant_id: str,
        date_str: str,
        start_time: str = "09:00",
        duration_minutes: int = 30,
    ) -> dict:
        """
        Check if a time slot is available.

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
            requested_start = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            requested_end = requested_start + timedelta(minutes=duration_minutes)

            # Get tenant's existing appointments
            tenant_appointments = self.appointments.get(tenant_id, [])

            # Check for conflicts
            conflicts = []
            for apt in tenant_appointments:
                if apt["status"] in ["CANCELLED", "COMPLETED"]:
                    continue

                apt_start = datetime.fromisoformat(apt["scheduled_datetime"])
                apt_end = apt_start + timedelta(minutes=apt.get("duration_minutes", 30))

                # Check for overlap
                if requested_start < apt_end and requested_end > apt_start:
                    conflicts.append(
                        {
                            "appointment_id": apt["appointment_id"],
                            "customer_name": apt["customer_name"],
                            "time": apt["scheduled_datetime"],
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
        Book a new appointment.

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

            # Create appointment
            appointment_id = str(uuid.uuid4())
            appointment = {
                "appointment_id": appointment_id,
                "tenant_id": tenant_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "scheduled_datetime": scheduled_datetime,
                "service_type": service_type,
                "duration_minutes": duration_minutes,
                "notes": notes,
                "status": "BOOKED",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Store appointment
            if tenant_id not in self.appointments:
                self.appointments[tenant_id] = []

            self.appointments[tenant_id].append(appointment)

            logger.info(
                f"Appointment booked | tenant={tenant_id} | appointment_id={appointment_id}"
            )

            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment": appointment,
            }

        except Exception as e:
            logger.error(f"Booking error: {e}")
            return {"status": "error", "error": str(e)}

    async def get_appointments(
        self, tenant_id: str, status: Optional[str] = None
    ) -> dict:
        """Get all appointments for a tenant."""
        try:
            appointments = self.appointments.get(tenant_id, [])

            if status:
                appointments = [apt for apt in appointments if apt["status"] == status]

            return {
                "status": "success",
                "count": len(appointments),
                "appointments": appointments,
            }

        except Exception as e:
            logger.error(f"Get appointments error: {e}")
            return {"status": "error", "error": str(e)}

    async def cancel_appointment(
        self, tenant_id: str, appointment_id: str, reason: str = ""
    ) -> dict:
        """Cancel an appointment."""
        try:
            appointments = self.appointments.get(tenant_id, [])

            appointment = None
            for apt in appointments:
                if apt["appointment_id"] == appointment_id:
                    appointment = apt
                    break

            if not appointment:
                return {"status": "error", "error": "Appointment not found"}

            appointment["status"] = "CANCELLED"
            appointment["cancellation_reason"] = reason
            appointment["cancelled_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                f"Appointment cancelled | tenant={tenant_id} | appointment_id={appointment_id}"
            )

            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment": appointment,
            }

        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            return {"status": "error", "error": str(e)}

    async def update_appointment_status(
        self, tenant_id: str, appointment_id: str, new_status: str
    ) -> dict:
        """Update appointment status."""
        try:
            appointments = self.appointments.get(tenant_id, [])

            appointment = None
            for apt in appointments:
                if apt["appointment_id"] == appointment_id:
                    appointment = apt
                    break

            if not appointment:
                return {"status": "error", "error": "Appointment not found"}

            appointment["status"] = new_status
            appointment["updated_at"] = datetime.now(timezone.utc).isoformat()

            return {
                "status": "success",
                "appointment_id": appointment_id,
                "appointment": appointment,
            }

        except Exception as e:
            logger.error(f"Update status error: {e}")
            return {"status": "error", "error": str(e)}

    async def get_daily_schedule(self, tenant_id: str, date_str: str) -> dict:
        """Get all appointments for a specific day."""
        try:
            appointments = self.appointments.get(tenant_id, [])

            # Filter by date
            daily_appointments = [
                apt
                for apt in appointments
                if apt["scheduled_datetime"].startswith(date_str)
                and apt["status"] != "CANCELLED"
            ]

            # Sort by time
            daily_appointments.sort(key=lambda x: x["scheduled_datetime"])

            return {
                "status": "success",
                "date": date_str,
                "count": len(daily_appointments),
                "appointments": daily_appointments,
            }

        except Exception as e:
            logger.error(f"Daily schedule error: {e}")
            return {"status": "error", "error": str(e)}


# Global instance
appointment_manager = AppointmentManager()
