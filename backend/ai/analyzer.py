"""Claude API client with prompt caching for NetSight analysis."""
import json
from typing import Any, Literal

import anthropic

from backend.config import settings
from backend.ai.prompts import diagnostic, log_triage, grafana as grafana_prompt


_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


AnalysisType = Literal["diagnostic", "log", "grafana", "capture"]

_PROMPTS = {
    "diagnostic": diagnostic.SYSTEM_PROMPT,
    "log": log_triage.SYSTEM_PROMPT,
    "grafana": grafana_prompt.SYSTEM_PROMPT,
    "capture": diagnostic.SYSTEM_PROMPT,
}


async def analyze(data: dict[str, Any], analysis_type: AnalysisType) -> dict[str, Any]:
    if not settings.ai_enabled:
        return {
            "root_cause": "AI analysis disabled — set ANTHROPIC_API_KEY in .env",
            "confidence": 0,
            "severity": "unknown",
            "findings": [],
            "recommended_commands": [],
            "escalation_path": "",
            "resolution_steps": [],
        }

    system_prompt = _PROMPTS.get(analysis_type, diagnostic.SYSTEM_PROMPT)

    try:
        client = _get_client()
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this data and return JSON:\n\n{json.dumps(data, indent=2, default=str)}",
                }
            ],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if model adds them despite instructions
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(raw)

    except json.JSONDecodeError as exc:
        return {
            "root_cause": "AI returned invalid JSON — raw response logged",
            "confidence": 0,
            "severity": "unknown",
            "findings": [f"Parse error: {exc}"],
            "recommended_commands": [],
            "escalation_path": "",
            "resolution_steps": [],
        }
    except Exception as exc:
        return {
            "root_cause": f"AI analysis failed: {exc}",
            "confidence": 0,
            "severity": "unknown",
            "findings": [],
            "recommended_commands": [],
            "escalation_path": "",
            "resolution_steps": [],
        }
