import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from database import get_db
from models import Business, Action, Conversation, Order
from action_queue import ActionQueueManager
from appointments import AppointmentManager
from payment_handoff import PaymentHandoffManager
from conversation_memory import ConversationMemory
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
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker container monitoring."""
    return {"status": "healthy", "service": "Perfect Assistant Backend"}


# ============================================================================
# ACTION QUEUE & DASHBOARD STREAMS
# ============================================================================

@app.websocket("/api/kds/{tenant_id}/stream")
async def action_stream(websocket: WebSocket, tenant_id: str, session: AsyncSession = Depends(get_db)):
    """WebSocket for real-time action updates to Kitchen Display System."""
    action_manager = ActionQueueManager(session)
    await action_manager.connect_monitor(tenant_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("event") == "COMPLETE_TICKET":
                order_id = data.get("order_id") or data.get("action_id")
                await action_manager.update_action_status(
                    tenant_id,
                    action_id=order_id,
                    new_status="COMPLETED",
                )
    except WebSocketDisconnect:
        action_manager.disconnect_monitor(tenant_id, websocket)


# ============================================================================
# APPOINTMENTS ENDPOINTS
# ============================================================================

@app.get("/api/appointments/{tenant_id}/availability")
async def check_appointment_availability(
    tenant_id: str,
    date: str,
    time: str = "09:00",
    duration_minutes: int = 30,
    session: AsyncSession = Depends(get_db)
):
    """Check if appointment time slot is available."""
    manager = AppointmentManager(session)
    result = await manager.check_availability(
        tenant_id, date, time, duration_minutes
    )
    return result


@app.post("/api/appointments/{tenant_id}/book")
async def book_appointment(
    tenant_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Book a new appointment."""
    body = await request.json()
    manager = AppointmentManager(session)
    result = await manager.book_appointment(
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
async def get_appointments(
    tenant_id: str,
    status: str = None,
    session: AsyncSession = Depends(get_db)
):
    """Get all appointments for a tenant."""
    manager = AppointmentManager(session)
    result = await manager.get_appointments(tenant_id, status)
    return result


@app.delete("/api/appointments/{tenant_id}/{appointment_id}")
async def cancel_appointment(
    tenant_id: str,
    appointment_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Cancel an appointment."""
    body = await request.json() if request.method == "DELETE" else {}
    manager = AppointmentManager(session)
    result = await manager.cancel_appointment(
        tenant_id, appointment_id, body.get("reason", "")
    )
    return result


@app.get("/api/appointments/{tenant_id}/schedule/{date}")
async def get_daily_schedule(
    tenant_id: str,
    date: str,
    session: AsyncSession = Depends(get_db)
):
    """Get all appointments for a specific day."""
    manager = AppointmentManager(session)
    result = await manager.get_daily_schedule(tenant_id, date)
    return result


# ============================================================================
# LEADS & PAYMENT HANDOFF
# ============================================================================

@app.get("/api/leads/{tenant_id}")
async def get_leads(
    tenant_id: str,
    status: str = None,
    session: AsyncSession = Depends(get_db)
):
    """Get all leads for a tenant."""
    manager = PaymentHandoffManager(session)
    result = await manager.get_leads(tenant_id, status)
    return result


@app.post("/api/leads/{tenant_id}")
async def create_lead(
    tenant_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Create a new lead from payment handoff."""
    body = await request.json()
    manager = PaymentHandoffManager(session)
    result = await manager.initiate_payment_handoff(
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
async def update_lead(
    tenant_id: str,
    lead_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Update lead status."""
    body = await request.json()
    manager = PaymentHandoffManager(session)
    result = await manager.update_lead_status(
        tenant_id, lead_id, body.get("status"), body.get("notes", "")
    )
    return result


@app.get("/api/leads/{tenant_id}/qualified")
async def get_qualified_leads(
    tenant_id: str,
    min_score: float = 0.6,
    session: AsyncSession = Depends(get_db)
):
    """Get high-quality leads ready for sales."""
    manager = PaymentHandoffManager(session)
    result = await manager.get_qualified_leads(tenant_id, min_score)
    return result


# ============================================================================
# ACTIONS (Orders, Appointments, Leads, Reservations)
# ============================================================================

@app.get("/api/actions/{tenant_id}")
async def get_recent_actions(
    tenant_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_db)
):
    """Get recent actions for a tenant."""
    manager = ActionQueueManager(session)
    actions = await manager.get_recent_actions(tenant_id, limit)
    return {"status": "success", "count": len(actions), "actions": actions}


@app.get("/dashboard/{tenant_id}/metrics")
async def get_metrics(
    tenant_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get real-time metrics for the dashboard."""
    try:
        # Get business config
        stmt = select(Business).where(Business.tenant_id == tenant_id)
        result = await session.execute(stmt)
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Count conversations from today
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        stmt_conversations = select(Conversation).where(
            (Conversation.tenant_id == tenant_id) &
            (Conversation.created_at >= today_start)
        )
        result_conversations = await session.execute(stmt_conversations)
        all_conversations = result_conversations.scalars().all()
        
        total_calls = len(all_conversations)
        ai_handled = sum(1 for c in all_conversations if not c.transferred_to_human)
        
        # Calculate average call duration
        avg_duration_seconds = 0
        if all_conversations:
            durations = [c.duration_seconds or 0 for c in all_conversations]
            avg_duration_seconds = int(sum(durations) / len(durations))
        
        minutes = avg_duration_seconds // 60
        seconds = avg_duration_seconds % 60
        avg_duration_str = f"{minutes}:{seconds:02d}"
        
        # Count orders from today (status = PICKED_UP or READY)
        stmt_orders = select(Order).where(
            (Order.tenant_id == tenant_id) &
            (Order.created_at >= today_start) &
            (Order.status.in_(["PICKED_UP", "READY"]))
        )
        result_orders = await session.execute(stmt_orders)
        orders_today = len(result_orders.scalars().all())
        
        return {
            "metrics": {
                "totalCalls": total_calls,
                "aiHandled": ai_handled,
                "avgDuration": avg_duration_str,
                "ordersToday": orders_today,
            },
            "phone_config": {
                "twilioNumber": business.twilio_number or "",
                "ownerPhone": business.owner_phone or "",
            },
            "ai_mode_enabled": business.ai_mode_enabled if business.ai_mode_enabled is not None else True,
            "active_call_sid": None,  # TODO: Track active calls in a separate table
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dashboard/{tenant_id}/phone-config")
async def save_phone_config(
    tenant_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Save phone configuration for a business."""
    try:
        body = await request.json()
        
        # Fetch business
        stmt = select(Business).where(Business.tenant_id == tenant_id)
        result = await session.execute(stmt)
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Update phone numbers
        business.twilio_number = body.get("twilioNumber", business.twilio_number)
        business.owner_phone = body.get("ownerPhone", business.owner_phone)
        business.updated_at = datetime.utcnow()
        
        await session.commit()
        
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Phone config save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/telephony/toggle-mode/{tenant_id}")
async def toggle_ai_mode(
    tenant_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Toggle between AI mode and live person mode."""
    try:
        body = await request.json()
        
        # Fetch business
        stmt = select(Business).where(Business.tenant_id == tenant_id)
        result = await session.execute(stmt)
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        mode = body.get("mode", "AI")
        business.ai_mode_enabled = (mode == "AI")
        business.updated_at = datetime.utcnow()
        
        await session.commit()
        
        return {
            "status": "success",
            "ai_mode_enabled": business.ai_mode_enabled,
            "mode": mode,
        }
    except Exception as e:
        logger.error(f"Mode toggle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
