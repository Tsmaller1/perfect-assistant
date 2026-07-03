import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware

from action_queue import action_queue
from appointments import appointment_manager
from payment_handoff import payment_handoff
from conversation_memory import conversation_memory
from telephony_router import router as telephony_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Perfect Assistant — AI Receptionist", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Lock down to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telephony_router)


# ============================================================================
# ACTION QUEUE & DASHBOARD STREAMS
# ============================================================================

@app.websocket("/api/kds/{tenant_id}/stream")
async def action_stream(websocket: WebSocket, tenant_id: str):
    """WebSocket for real-time action updates to admin dashboard."""
    await action_queue.connect_monitor(tenant_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("event") == "COMPLETE_TICKET":
                await action_queue.update_action_status(
                    tenant_id,
                    action_id=data["action_id"],
                    new_status="COMPLETED",
                )
    except WebSocketDisconnect:
        action_queue.disconnect_monitor(tenant_id, websocket)


# ============================================================================
# APPOINTMENTS ENDPOINTS
# ============================================================================

@app.get("/api/appointments/{tenant_id}/availability")
async def check_appointment_availability(
    tenant_id: str,
    date: str,
    time: str = "09:00",
    duration_minutes: int = 30
):
    """Check if appointment time slot is available."""
    result = await appointment_manager.check_availability(
        tenant_id, date, time, duration_minutes
    )
    return result


@app.post("/api/appointments/{tenant_id}/book")
async def book_appointment(tenant_id: str, request: Request):
    """Book a new appointment."""
    body = await request.json()
    result = await appointment_manager.book_appointment(
        tenant_id=tenant_id,
        customer_name=body.get("customer_name"),
        customer_email=body.get("customer_email"),
        customer_phone=body.get("customer_phone"),
        scheduled_datetime=body.get("scheduled_datetime"),
        service_type=body.get("service_type", "General"),
        duration_minutes=body.get("duration_minutes", 30),
        notes=body.get("notes", ""),
    )
    return result


@app.get("/api/appointments/{tenant_id}")
async def get_appointments(tenant_id: str, status: str = None):
    """Get all appointments for a tenant."""
    result = await appointment_manager.get_appointments(tenant_id, status)
    return result


@app.delete("/api/appointments/{tenant_id}/{appointment_id}")
async def cancel_appointment(tenant_id: str, appointment_id: str, request: Request):
    """Cancel an appointment."""
    body = await request.json() if request.method == "DELETE" else {}
    result = await appointment_manager.cancel_appointment(
        tenant_id, appointment_id, body.get("reason", "")
    )
    return result


@app.get("/api/appointments/{tenant_id}/schedule/{date}")
async def get_daily_schedule(tenant_id: str, date: str):
    """Get all appointments for a specific day."""
    result = await appointment_manager.get_daily_schedule(tenant_id, date)
    return result


# ============================================================================
# LEADS & PAYMENT HANDOFF
# ============================================================================

@app.get("/api/leads/{tenant_id}")
async def get_leads(tenant_id: str, status: str = None):
    """Get all leads for a tenant."""
    result = await payment_handoff.get_leads(tenant_id, status)
    return result


@app.post("/api/leads/{tenant_id}")
async def create_lead(tenant_id: str, request: Request):
    """Create a new lead from payment handoff."""
    body = await request.json()
    result = await payment_handoff.initiate_payment_handoff(
        tenant_id=tenant_id,
        call_sid=body.get("call_sid"),
        owner_phone=body.get("owner_phone"),
        customer_name=body.get("customer_name"),
        customer_phone=body.get("customer_phone"),
        customer_email=body.get("customer_email"),
        order_value=body.get("order_value"),
        order_items=body.get("order_items"),
        notes=body.get("notes", ""),
    )
    return result


@app.patch("/api/leads/{tenant_id}/{lead_id}")
async def update_lead(tenant_id: str, lead_id: str, request: Request):
    """Update lead status."""
    body = await request.json()
    result = await payment_handoff.update_lead_status(
        tenant_id, lead_id, body.get("status"), body.get("notes", "")
    )
    return result


@app.get("/api/leads/{tenant_id}/qualified")
async def get_qualified_leads(tenant_id: str, min_score: float = 0.6):
    """Get high-quality leads ready for sales."""
    result = await payment_handoff.get_qualified_leads(tenant_id, min_score)
    return result


# ============================================================================
# ACTIONS (Orders, Appointments, Leads, Reservations)
# ============================================================================

@app.get("/api/actions/{tenant_id}")
async def get_recent_actions(tenant_id: str, limit: int = 50):
    """Get recent actions for a tenant."""
    actions = action_queue.get_recent_actions(tenant_id, limit)
    return {"status": "success", "count": len(actions), "actions": actions}


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
