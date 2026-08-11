"""Unit tests for business-scope heuristics (agent-scope-01/02)."""

from __future__ import annotations

import pytest

from app.kb_service import DomainError
from app.scope_guard import check_business_scope


def test_should_reject_strategy_request_zh():
    with pytest.raises(DomainError) as ei:
        check_business_scope("请根据本周数据给出投放策略")
    assert ei.value.code == "OUT_OF_SCOPE_BUSINESS_REASONING"
    assert ei.value.degrade_hint


def test_should_reject_strategy_request_en():
    with pytest.raises(DomainError) as ei:
        check_business_scope(None, "Please generate a campaign strategy for HCPs")
    assert ei.value.code == "OUT_OF_SCOPE_BUSINESS_REASONING"


def test_should_reject_open_decision_zh():
    with pytest.raises(DomainError) as ei:
        check_business_scope("研究完直接告诉我该怎么做")
    assert ei.value.code == "OUT_OF_SCOPE_BUSINESS_REASONING"


def test_should_reject_open_decision_en():
    with pytest.raises(DomainError) as ei:
        check_business_scope("just tell me what to do after you research")
    assert ei.value.code == "OUT_OF_SCOPE_BUSINESS_REASONING"


def test_should_allow_knowledge_about_strategy_topic():
    # Documenting past strategy notes is in scope; generating one is not.
    check_business_scope("HCP 投放策略备忘 2024")
    check_business_scope(None, None)
