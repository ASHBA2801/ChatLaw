"""Unit tests for the local clarification interview (no live Gemini)."""

from conversation.interview import InterviewManager, InterviewResult
from conversation.languages import language_name, normalize_language


def test_tenancy_deposit_query_asks_clarification():
    mgr = InterviewManager()
    result = mgr.process_turn("I need help with a tenancy deposit problem", language="en")
    assert result.action == "clarify"
    assert result.question
    assert result.state["domain"] == "tenancy"
    assert result.state["round"] == 1
    assert "party_role" in result.state["asked"]
    assert "deposit" in (result.state.get("slots") or {}).get("issue_type", "").lower() or \
           "issue_type" not in result.state.get("asked", [])


def test_follow_up_fills_slot_and_may_ask_or_proceed():
    mgr = InterviewManager()
    first = mgr.process_turn("My landlord is causing trouble with the rental", language="en")
    assert first.action == "clarify"
    asked = first.state["asked"][-1]

    second = mgr.process_turn("I am the tenant and this is about the deposit", language="en", prior_interview_state=first.state)
    assert "party_role" in second.state["slots"] or asked in second.state["slots"]
    assert second.action in ("clarify", "answer")
    if second.action == "clarify":
        assert second.question
        assert second.state["round"] == 2
    else:
        assert second.assembled_situation
        assert "deposit" in second.assembled_situation.lower() or "tenant" in second.assembled_situation.lower()


def test_max_three_rounds_then_answer():
    mgr = InterviewManager()
    state = None
    actions = []
    replies = [
        "There is a tenancy dispute about my rented house",
        "not sure yet",
        "not sure yet",
        "not sure yet",
        "not sure yet",
    ]
    for message in replies:
        result = mgr.process_turn(message, language="en", prior_interview_state=state)
        actions.append(result.action)
        state = result.state
        if result.action == "answer":
            break
    assert actions.count("clarify") == InterviewManager.MAX_ROUNDS
    assert actions[-1] == "answer"
    assert state["round"] == InterviewManager.MAX_ROUNDS
    assert state.get("assumptions")


def test_section_lookup_skips_interview():
    mgr = InterviewManager()
    result = mgr.process_turn("What is the punishment for theft under BNS section 303?", language="en")
    assert result.action == "answer"
    assert result.question is None
    assert result.assembled_situation


def test_tamil_and_hindi_clarification_not_english():
    mgr = InterviewManager()
    prompt = "I have a tenancy problem with my rental house"
    ta = mgr.process_turn(prompt, language="ta")
    en = mgr.process_turn(prompt, language="en")
    assert ta.action == "clarify"
    assert ta.question
    assert ta.question != en.question
    assert any("\u0b80" <= ch <= "\u0bff" for ch in ta.question)

    hi = mgr.process_turn(prompt, language="hi")
    assert hi.action == "clarify"
    assert hi.question
    assert any("\u0900" <= ch <= "\u097f" for ch in hi.question)


def test_process_turn_clarify_does_not_need_generator():
    """Clarification is fully local — no generator/Gemini required."""
    mgr = InterviewManager()
    result = mgr.process_turn("Need help with my employment workplace salary issue", language="en")
    assert isinstance(result, InterviewResult)
    assert result.action == "clarify"
    assert result.question
    # No exception and no external calls — state is persistable.
    assert set(result.state) >= {"domain", "round", "max_rounds", "slots", "asked", "assumptions", "original_query"}


def test_normalize_language_and_names():
    assert normalize_language("HI") == "hi"
    assert normalize_language("ta-IN") == "ta"
    assert normalize_language("unknown") == "en"
    assert language_name("ta") == "Tamil"


def test_english_fallback_for_missing_eighth_schedule_translations():
    mgr = InterviewManager()
    # Assamese has no dedicated questions — should fall back to English text.
    result = mgr.process_turn("I have a tenancy problem with my rental house", language="as")
    assert result.action == "clarify"
    en = mgr.process_turn("I have a tenancy problem with my rental house", language="en")
    assert result.question == en.question
