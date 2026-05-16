"""Running QA service — answers user questions with compact context."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from running_coach.llm import LlmError, OpenAICompatibleClient
from running_coach.storage import ProjectStorage
from running_coach.services.qa_context import build_qa_context, format_qa_prompt


_FALLBACK_ANSWER = (
    "Сейчас не могу получить ответ от тренера — LLM недоступен. "
    "Попробуй повторить позже или уточни вопрос."
)

_MEDICAL_KEYWORDS = (
    "боль в груди", "сердце", "обморок", "потерял сознание",
    "острая боль", "не могу дышать", "сильная одышка", "травма",
)


def answer_running_question(
    storage: ProjectStorage,
    client: OpenAICompatibleClient,
    question: str,
    *,
    prompt_path: Path,
    today: date | None = None,
) -> dict[str, Any]:
    """Build context, call LLM, return structured answer."""

    warnings: list[str] = []
    if _has_medical_flag(question):
        warnings.append(
            "Обнаружены симптомы, требующие медицинской консультации. "
            "Прекрати тренировку и обратись к врачу."
        )

    context = build_qa_context(storage, question, today=today)
    prompt_template = prompt_path.read_text(encoding="utf-8").strip()
    system_prompt = format_qa_prompt(context, prompt_template)

    try:
        answer = client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ])
    except LlmError:
        return {
            "agent": "running-qa-agent",
            "status": "llm_unavailable",
            "answer": _FALLBACK_ANSWER,
            "warnings": warnings,
        }

    return {
        "agent": "running-qa-agent",
        "status": "completed",
        "answer": answer.strip(),
        "warnings": warnings,
    }


def format_qa_response(result: dict[str, Any]) -> str:
    """Format QA result for Telegram."""
    lines: list[str] = []
    if result.get("warnings"):
        for w in result["warnings"]:
            lines.append(f"⚠ {w}")
        lines.append("")
    lines.append(result.get("answer") or _FALLBACK_ANSWER)
    return "\n".join(lines)


def _has_medical_flag(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _MEDICAL_KEYWORDS)
