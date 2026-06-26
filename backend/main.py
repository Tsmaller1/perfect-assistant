import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from kds_manager import kds_manager
from telephony_router import router as telephony_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Pine Sales AI — KDS Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Lock down to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telephony_router)


@app.websocket("/api/kds/{tenant_id}/stream")
async def kds_stream(websocket: WebSocket, tenant_id: str):
    await kds_manager.connect_kitchen_monitor(tenant_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("event") == "COMPLETE_TICKET":
                await kds_manager.send_ticket_update(
                    tenant_id,
                    order_id=data["order_id"],
                    status="COMPLETE",
                )
    except WebSocketDisconnect:
        kds_manager.disconnect_kitchen_monitor(tenant_id, websocket)


@app.get("/dashboard/{tenant_id}/metrics")
async def get_metrics(tenant_id: str):
    # Stub — replace with real DB queries
    return {
        "metrics": {
            "totalCalls": 24,
            "aiHandled": 19,
            "avgDuration": "3:42",
            "ordersToday": 17,
        },
        "phone_config": {
            "twilioNumber": "",
            "ownerPhone": "",
        },
        "ai_mode_enabled": True,
        "active_call_sid": None,
    }


@app.post("/dashboard/{tenant_id}/phone-config")
async def save_phone_config(tenant_id: str):
    # Stub — persist to DB
    return {"status": "saved"}
