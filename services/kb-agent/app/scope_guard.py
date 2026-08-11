"""Intent heuristics for agent-scope-01 / agent-scope-02.

Rejects requests that ask kb-agent to produce business strategy or final
open-ended decisions. Storing knowledge *about* strategy is allowed when the
text does not read as an instruction to generate one.
"""

from __future__ import annotations

import re

from app.kb_service import DomainError

DEGRADE_HINT = (
    "You may search the private library (or public sources) for evidence only; "
    "business strategy and final decisions must be made by the caller LLM."
)

# Action-oriented: ask the agent to produce strategy / campaign plans.
_STRATEGY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"(给出|生成|制定|输出).{0,12}(投放)?策略",
        r"(投放策略|营销策略|获客策略).{0,8}(给我|帮我|请)",
        r"(帮我|请).{0,12}(投放|营销|获客).{0,8}策略",
        r"(give|generate|create|write|produce).{0,20}(campaign |go[- ]to[- ]market |gtm |ad |ads |marketing )?strateg(y|ies)",
        r"(campaign|marketing|gtm).{0,12}(plan|strategy).{0,12}(for me|please)",
        r"what (ads|campaigns?) should (we|i) (run|buy)",
    )
]

# Open-ended “decide for me”.
_OPEN_DECISION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"(直接)?告诉我该怎么做",
        r"帮我(决定|拍板|定夺)",
        r"研究完.{0,8}(直接)?告诉我",
        r"(just )?tell me what (to|I should) do",
        r"what should (we|i) do\b",
        r"(make|give) (me )?(the )?final (decision|call|recommendation)\b",
        r"decide (for|instead of) me",
    )
]


def check_business_scope(*parts: str | None) -> None:
    """Raise DomainError if any part asks for strategy or an open decision."""
    blob = "\n".join((p or "").strip() for p in parts if (p or "").strip())
    if not blob:
        return
    for pat in _STRATEGY_PATTERNS:
        if pat.search(blob):
            raise DomainError(
                "OUT_OF_SCOPE_BUSINESS_REASONING",
                "Business strategy / campaign conclusions are out of scope for kb-agent.",
                degrade_hint=DEGRADE_HINT,
            )
    for pat in _OPEN_DECISION_PATTERNS:
        if pat.search(blob):
            raise DomainError(
                "OUT_OF_SCOPE_BUSINESS_REASONING",
                "Open-ended business decisions are out of scope; return evidence only.",
                degrade_hint=DEGRADE_HINT,
            )
