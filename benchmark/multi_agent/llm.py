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
            content = str(response["choices"][0]["message"]["content"])
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {"note": content}
            findings = tuple(item for item in parsed.get("findings", []) if isinstance(item, dict))
            questions = tuple(str(item) for item in parsed.get("follow_up_questions", []) if str(item).strip())
            note = str(parsed.get("note", ""))
            return replace(
                AgentResult.now(agent.agent_id, "completed", note=note),
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
