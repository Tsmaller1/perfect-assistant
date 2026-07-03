import json
import logging
from typing import Optional

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import Connect, VoiceResponse

from agent_engine import build_agent_session
from action_queue import action_queue, ActionType
from scraper_enhanced import scrape_business_website

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telephony", tags=["Telephony"])

# Load from environment variables in production
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN  = "your_auth_token"
TWILIO_CLIENT      = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def _get_tenant_config(tenant_id: str) -> dict:
    """Stub — replace with real DB lookup."""
    return {
        "business_name": "Demo Restaurant",
        "ai_mode_enabled": True,
        "owner_phone": "+15550001111",
        "twilio_number": "+15559990000",
    }


@router.post("/incoming/{tenant_id}")
async def handle_incoming_call(tenant_id: str, request: Request) -> Response:
    config = _get_tenant_config(tenant_id)
    vr = VoiceResponse()
    if config["ai_mode_enabled"]:
        vr.say(f"Thanks for calling {config['business_name']}! One moment please.")
        connect = Connect()
        connect.stream(url=f"wss://yourserver.com/telephony/ai-stream/{tenant_id}")
        vr.append(connect)
    else:
        vr.dial(config["owner_phone"])
    return Response(content=str(vr), media_type="application/xml")


@router.websocket("/ai-stream/{tenant_id}")
async def ai_media_stream(websocket: WebSocket, tenant_id: str):
    await websocket.accept()
    config  = _get_tenant_config(tenant_id)
    session = build_agent_session(tenant_id, config)
    call_sid: Optional[str] = None
    try:
        async for raw in websocket.iter_text():
            data       = json.loads(raw)
            event_type = data.get("event")
            if event_type == "start":
                call_sid = data["start"]["callSid"]
                session.set_call_sid(call_sid)
            elif event_type == "media":
                audio_chunk = data["media"]["payload"]
                response_audio, fn_calls = await session.process_audio(audio_chunk)
                for fn in fn_calls:
                    fn_name = fn["name"]
                    args = fn["arguments"]
                    
                    # Handle different function calls
                    if fn_name == "submit_kitchen_order":
                        # Backward compatible - orders still work
                        await action_queue.broadcast_order(tenant_id, args)
                    elif fn_name == "submit_action":
                        # New generic action handler
                        action_type = args.get("action_type", "ORDER")
                        await action_queue.broadcast_new_action(
                            tenant_id,
                            ActionType(action_type),
                            args.get("customer_info", {}),
                            args.get("action_data", {})
                        )
                    elif fn_name == "create_lead":
                        # Create a lead action
                        await action_queue.broadcast_new_action(
                            tenant_id,
                            ActionType.LEAD,
                            {
                                "name": args.get("customer_name", ""),
                                "phone": args.get("customer_phone", ""),
                                "email": args.get("customer_email", ""),
                            },
                            {
                                "notes": args.get("notes", ""),
                                "qualification_score": args.get("qualification_score", 0.5),
                            }
                        )
                
                if response_audio:
                    await websocket.send_text(
                        json.dumps({"event": "media", "media": {"payload": response_audio}})
                    )
            elif event_type == "stop":
                break
            elif event_type == "interrupt_transfer" and call_sid:
                await _hot_transfer(call_sid, config["owner_phone"], tenant_id)
                break
    except WebSocketDisconnect:
        logger.info("Twilio WS disconnected | tenant=%s", tenant_id)
    finally:
        await session.close()


async def _hot_transfer(call_sid: str, owner_phone: str, tenant_id: str) -> None:
    vr = VoiceResponse()
    vr.say("Please hold, connecting you to our team now.")
    vr.dial(owner_phone)
    TWILIO_CLIENT.calls(call_sid).update(twiml=str(vr))
    logger.info("Hot-transfer | tenant=%s | call=%s | to=%s", tenant_id, call_sid, owner_phone)


@router.post("/toggle-mode/{tenant_id}")
async def toggle_mode(tenant_id: str, request: Request):
    body     = await request.json()
    mode     = body.get("mode")
    call_sid = body.get("active_call_sid")
    if mode == "LIVE_PERSON" and call_sid:
        config = _get_tenant_config(tenant_id)
        await _hot_transfer(call_sid, config["owner_phone"], tenant_id)
        return {"status": "transferred", "call_sid": call_sid}
    return {"status": "mode_updated", "mode": mode}


@router.post("/businesses/{tenant_id}/onboard")
async def onboard_business(tenant_id: str, request: Request):
    """
    Onboard a new business by scraping their website.
    
    Request body:
    {
        "website_url": "https://i10education.com"
    }
    """
    try:
        body = await request.json()
        website_url = body.get("website_url", "")

        if not website_url:
            return {"status": "error", "error": "website_url required"}

        logger.info(f"Onboarding business {tenant_id} | URL: {website_url}")

        # Scrape the website
        scrape_result = await scrape_business_website(website_url, tenant_id)

        if scrape_result["status"] != "success":
            return {
                "status": "error",
                "error": f"Failed to scrape website: {scrape_result.get('error', 'Unknown error')}",
            }

        # Extract scraped data
        business_data = scrape_result["data"]

        # In a real app, save to database here
        # For now, just return the data
        logger.info(f"Onboarding complete for {tenant_id}")

        return {
            "status": "success",
            "tenant_id": tenant_id,
            "business_profile": business_data,
            "ai_context": business_data.get("ai_context", ""),
        }

    except Exception as e:
        logger.error(f"Onboarding error for {tenant_id}: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/businesses/{tenant_id}/profile")
async def get_business_profile(tenant_id: str):
    """Retrieve scraped business profile for a tenant."""
    try:
        # In a real app, retrieve from database
        # For now, return stub data
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "business_profile": {
                "business": {
                    "name": "Demo Business",
                    "phone": "+15559990000",
                },
                "ai_context": "Demo business context",
            },
        }
    except Exception as e:
        logger.error(f"Profile retrieval error for {tenant_id}: {e}")
        return {"status": "error", "error": str(e)}

