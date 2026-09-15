from __future__ import annotations

import asyncio
import json
import os
from dataclasses import replace
from urllib.request import Request, urlopen

from .models import AgentResult, AgentSpec, ResearchProgram


class OpenAICompatibleExecutor:
    """Minimal provider-neutral chat adapter for an OpenAI-compatible endpoint."""

    def __init__(self, endpoint: str, api_key: str, model: str, timeout_seconds: int = 180) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("LLM endpoint must be HTTP(S)")
        if not api_key.strip() or not model.strip():
            raise ValueError("LLM api key and model are required")
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def __call__(self, program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
        prompt = {
            "program": program.question,
            "program_title": program.title,
            "role": agent.role,
            "role_objective": agent.objective,
            "source_families": list(agent.source_families),
            "shared_context": context,
            "output_contract": {
                "findings": "array of concise evidence-backed findings; include source URLs when actually known",
                "follow_up_questions": "array of unresolved high-value questions",
                "note": "brief quality/caveat note",
            },
        }
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are one bounded research agent in a multi-agent research system. Do not invent browsing or evidence. Clearly distinguish discovered evidence from hypotheses.",
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                "temperature": 0,
            }
        ).encode("utf-8")
        request = Request(
            f"{self.endpoint}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )

        def call() -> dict[str, object]:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            response = await asyncio.to_thread(call)
            content = response["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("LLM response content is missing or empty")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("LLM response must be a JSON object")
            findings_raw = parsed.get("findings", [])
            questions_raw = parsed.get("follow_up_questions", [])
            note_raw = parsed.get("note", "")
            if not isinstance(findings_raw, list) or not all(isinstance(item, dict) for item in findings_raw):
                raise ValueError("LLM findings must be an array of objects")
            if not isinstance(questions_raw, list) or not all(isinstance(item, str) for item in questions_raw):
                raise ValueError("LLM follow_up_questions must be an array of strings")
            if not isinstance(note_raw, str):
                raise ValueError("LLM note must be a string")
            findings = tuple(findings_raw)
            questions = tuple(item for item in questions_raw if item.strip())
            return replace(
                AgentResult.now(agent.agent_id, "completed", note=note_raw),
                findings=findings,
                follow_up_questions=questions,
            )
        except Exception as exc:
            return AgentResult.now(agent.agent_id, "failed", note=f"{type(exc).__name__}: {exc}")


def configured_executor() -> OpenAICompatibleExecutor | None:
    endpoint = os.getenv("RESEARCH_LLM_ENDPOINT", "").strip()
    key = os.getenv("RESEARCH_LLM_API_KEY", "").strip()
    model = os.getenv("RESEARCH_LLM_MODEL", "").strip()
    if not endpoint or not key or not model:
        return None
    return OpenAICompatibleExecutor(endpoint, key, model)
