import base64
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import openai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a friendly, efficient phone order agent for {business_name}.
Collect all order items and the customer name, then call submit_kitchen_order.
Never end the call until the order is confirmed and submitted.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "submit_kitchen_order",
            "description": "Submit a completed phone order to the kitchen display system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name":         {"type": "string"},
                    "customer_phone":        {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name":          {"type": "string"},
                                "quantity":      {"type": "integer"},
                                "customization": {"type": "string"},
                            },
                            "required": ["name", "quantity"],
                        },
                    },
                    "special_instructions": {"type": "string"},
                },
                "required": ["customer_name", "items"],
            },
        },
    }
]


@dataclass
class AgentSession:
    tenant_id: str
    config: dict
    call_sid: Optional[str] = None
    _client: Any = field(init=False, repr=False)

    def __post_init__(self):
        self._client = openai.AsyncOpenAI()
        self._conversation = [
            {"role": "system",
             "content": SYSTEM_PROMPT.format(
                 business_name=self.config.get("business_name", "our restaurant"))}
        ]

    def set_call_sid(self, sid: str) -> None:
        self.call_sid = sid

    async def process_audio(self, audio_b64: str) -> tuple[Optional[str], list[dict]]:
        audio_bytes = base64.b64decode(audio_b64)
        transcript  = await self._client.audio.transcriptions.create(
            model="whisper-1", file=("audio.raw", audio_bytes, "audio/x-raw"))
        if not transcript.text.strip():
            return None, []

        self._conversation.append({"role": "user", "content": transcript.text})
        completion = await self._client.chat.completions.create(
            model="gpt-4o", messages=self._conversation,
            tools=TOOLS, tool_choice="auto")
        msg = completion.choices[0].message
        self._conversation.append(msg)

        if msg.tool_calls:
            return None, [{"name": tc.function.name,
                           "arguments": json.loads(tc.function.arguments)}
                          for tc in msg.tool_calls]

        tts = await self._client.audio.speech.create(
            model="tts-1", voice="alloy",
            input=msg.content or "", response_format="ulaw")
        return base64.b64encode(tts.content).decode(), []

    async def close(self) -> None:
        logger.info("Session closed | tenant=%s | call=%s", self.tenant_id, self.call_sid)


def build_agent_session(tenant_id: str, config: dict) -> AgentSession:
    return AgentSession(tenant_id=tenant_id, config=config)
