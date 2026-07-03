"""
ActionQueue Manager — Generalized from KDS system
Handles all action types: orders, appointments, leads, reservations
Broadcasts via WebSocket to business admin dashboards
"""

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    ORDER = "ORDER"
    APPOINTMENT = "APPOINTMENT"
    LEAD = "LEAD"
    RESERVATION = "RESERVATION"


class ActionStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ActionQueueManager:
    """
    Manages persistent WebSocket connections for per-tenant action monitors.
    Broadcasts real-time updates for orders, appointments, leads, reservations.
    """

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._action_history: dict[str, list[dict]] = defaultdict(list)

    async def connect_monitor(self, tenant_id: str, websocket: WebSocket) -> None:
        """Connect a new admin monitor (dashboard) for a tenant."""
        await websocket.accept()
        self._connections[tenant_id].add(websocket)
        logger.info(
            "Admin monitor connected | tenant=%s | total=%d",
            tenant_id,
            len(self._connections[tenant_id]),
        )

    def disconnect_monitor(self, tenant_id: str, websocket: WebSocket) -> None:
        """Disconnect an admin monitor."""
        self._connections[tenant_id].discard(websocket)
        logger.info(
            "Admin monitor disconnected | tenant=%s | remaining=%d",
            tenant_id,
            len(self._connections[tenant_id]),
        )

    async def broadcast_new_action(
        self,
        tenant_id: str,
        action_type: ActionType,
        customer_info: dict[str, Any],
        action_data: dict[str, Any],
    ) -> str:
        """
        Broadcast a new action to all connected monitors.

        Args:
            tenant_id: Business tenant ID
            action_type: Type of action (ORDER, APPOINTMENT, LEAD, RESERVATION)
            customer_info: {name, email, phone, etc.}
            action_data: Action-specific data (items, datetime, notes, etc.)

        Returns:
            action_id (UUID string)
        """
        action_id = str(uuid.uuid4())

        # Build action payload
        action = {
            "action_id": action_id,
            "action_type": action_type.value,
            "customer_info": customer_info,
            "action_data": action_data,
            "status": ActionStatus.NEW.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store in history
        self._action_history[tenant_id].append(action)

        # Broadcast to all connected monitors
        payload = {"event": "NEW_ACTION", "action": action}
        message = json.dumps(payload)

        dead: list[WebSocket] = []
        for ws in list(self._connections.get(tenant_id, [])):
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to monitor: {e}")
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect_monitor(tenant_id, ws)

        logger.info(
            "Action broadcasted | tenant=%s | type=%s | action_id=%s",
            tenant_id,
            action_type.value,
            action_id,
        )

        return action_id

    async def update_action_status(
        self, tenant_id: str, action_id: str, new_status: ActionStatus, notes: Optional[str] = None
    ) -> None:
        """
        Update action status and broadcast to monitors.

        Args:
            tenant_id: Business tenant ID
            action_id: Action ID to update
            new_status: New status (IN_PROGRESS, COMPLETED, FAILED)
            notes: Optional status notes
        """
        # Find action in history
        action = None
        for act in self._action_history.get(tenant_id, []):
            if act["action_id"] == action_id:
                action = act
                break

        if not action:
            logger.warning(f"Action not found: {action_id}")
            return

        # Update action
        action["status"] = new_status.value
        action["updated_at"] = datetime.now(timezone.utc).isoformat()
        if notes:
            action["notes"] = notes

        # Broadcast update
        payload = {"event": "ACTION_UPDATE", "action_id": action_id, "action": action}
        message = json.dumps(payload)

        dead: list[WebSocket] = []
        for ws in list(self._connections.get(tenant_id, [])):
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast update: {e}")
                dead.append(ws)

        for ws in dead:
            self.disconnect_monitor(tenant_id, ws)

        logger.info(
            "Action updated | tenant=%s | action_id=%s | status=%s",
            tenant_id,
            action_id,
            new_status.value,
        )

    async def broadcast_order(self, tenant_id: str, order_details: dict[str, Any]) -> str:
        """Convenience method for orders (backward compatible with KDS)."""
        customer_info = {
            "name": order_details.get("customer_name", "Guest"),
            "phone": order_details.get("customer_phone", ""),
        }
        action_data = {
            "items": order_details.get("items", []),
            "special_instructions": order_details.get("special_instructions", ""),
        }
        return await self.broadcast_new_action(
            tenant_id, ActionType.ORDER, customer_info, action_data
        )

    async def send_ticket_update(
        self, tenant_id: str, order_id: str, status: str
    ) -> None:
        """Convenience method for status updates (backward compatible with KDS)."""
        await self.update_action_status(
            tenant_id, order_id, ActionStatus(status.upper())
        )

    def get_recent_actions(self, tenant_id: str, limit: int = 50) -> list[dict]:
        """Retrieve recent actions for a tenant."""
        return self._action_history.get(tenant_id, [])[-limit:]


# Global instance (same pattern as KDS)
action_queue = ActionQueueManager()
