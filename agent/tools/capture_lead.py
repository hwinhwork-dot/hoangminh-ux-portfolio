"""Tool: capture_lead — the only tool permitted outbound network access.

Fires when a visitor signals hiring intent. It records that someone asked, and what they
asked — never who they are, because the studio collects no identity and should not start
now. Failure is silent by design: a webhook outage must not change what the visitor sees.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

from agent.config import get_settings


async def capture_lead(session_id: str, question: str, intent: str) -> bool:
    record = {
        "event": "lead",
        "ts": datetime.now(UTC).isoformat(),
        "session": session_id,
        "intent": intent,
        "question": question[:200],
    }
    print(json.dumps(record, ensure_ascii=False), file=sys.stdout, flush=True)

    url = get_settings().lead_webhook_url
    if not url:
        return False
    try:
        import httpx

        async with httpx.AsyncClient(timeout=4.0) as client:
            await client.post(url, json=record)
        return True
    except Exception:
        return False
