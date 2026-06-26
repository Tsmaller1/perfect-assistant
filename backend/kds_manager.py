import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class KitchenDisplayManager:
    """
    Manages persistent WebSocket connections for per-tenant kitchen monitors.
    Supports multiple monitors per tenant (e.g., grill + expo station).
    """

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect_kitchen_monitor(self, tenant_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[tenant_id].add(websocket)
        logger.info("Kitchen monitor connected | tenant=%s | total=%d",
                    tenant_id, len(self._connections[tenant_id]))

    def disconnect_kitchen_monitor(self, tenant_id: str, websocket: WebSocket) -> None:
        self._connections[tenant_id].discard(websocket)
        logger.info("Kitchen monitor disconnected | tenant=%s | remaining=%d",
                    tenant_id, len(self._connections[tenant_id]))

    async def broadcast_new_order(self, tenant_id: str, order_details: dict[str, Any]) -> None:
        payload = {
            "event": "NEW_ORDER",
            "ticket": {
                "order_id": order_details.get("order_id"),
                "customer_name": order_details.get("customer_name", "Guest"),
                "customer_phone": order_details.get("customer_phone", ""),
                "items": order_details.get("items", []),
                "special_instructions": order_details.get("special_instructions", ""),
                "received_at": datetime.now(timezone.utc).isoformat(),
                "status": "OPEN",
            },
        }
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(tenant_id, [])):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_kitchen_monitor(tenant_id, ws)

    async def send_ticket_update(self, tenant_id: str, order_id: str, status: str) -> None:
        payload = json.dumps({
            "event": "TICKET_UPDATE",
            "order_id": order_id,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(tenant_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_kitchen_monitor(tenant_id, ws)


kds_manager = KitchenDisplayManager()
