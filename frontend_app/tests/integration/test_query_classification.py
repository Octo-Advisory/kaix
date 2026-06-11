
"""Integration tests for the parse_llm_response sites in
Ai_module/Query_Classification_And_Analysis.py:

  1. refine_query_with_history (~line 502)  → RefinedQuery
  2. classify_query_multilabel (~line 2480) → IntentClassification

Both functions take `llm` as a parameter and build an internal LangChain
chain (prompt | llm) before passing the result to parse_llm_response.
For the chain to execute end-to-end without hitting Groq, we pass a
RunnableLambda that pops canned strings on every .invoke() call —
serving both the initial chain invocation AND the parse_llm_response
corrective retry.

Stubs:
  llm                → RunnableLambda with a canned-response queue
  qca.get_chat       → returns []  (avoids Redis)
"""

from langchain_core.runnables import RunnableLambda

from frontend_app.Ai_module import Query_Classification_And_Analysis as qca


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeMessage:
    """Stand-in for langchain_core.messages.AIMessage — only .content
    is read downstream (raw_output = getattr(result, 'content', ...))."""
    def __init__(self, content):
        self.content = content


def _make_runnable_llm(responses):
    """Build a Runnable that pops the next canned response on every
    .invoke() call. Returns (runnable, calls_list) so tests can inspect
    how many times the LLM was hit and with what."""
    queue = list(responses)
    calls = []

    def _fn(input_, **kwargs):
        calls.append((input_, kwargs))
        if not queue:
            raise IndexError(
                f"fake llm exhausted after {len(calls)} calls; "
                "test queued too few responses"
            )
        return _FakeMessage(queue.pop(0))

    return RunnableLambda(_fn), calls


# ===========================================================================
# refine_query_with_history
# ===========================================================================

def test_refine_query_with_history_happy(log_error_calls):
    # ONE canned response — parse_llm_response succeeds on first parse,
    # the corrective retry never fires.
    llm, calls = _make_runnable_llm([
        '{"refined_query": "What vendors supply steel in Pune?"}'
    ])

    result = qca.refine_query_with_history(
        history=["user: hi", "assistant: hello"],
        latest_query="any steel vendors?",
        llm=llm,
    )

    # On success the function returns the validated string (not a model).
    assert isinstance(result, str)
    assert "Pune" in result
    assert len(calls) == 1                # only the chain.invoke — no retry
    assert log_error_calls == []          # nothing went wrong


def test_refine_query_with_history_failure(log_error_calls):
    # TWO canned responses: 1st for the chain.invoke, 2nd for the
    # parse_llm_response corrective retry. Both fail to validate as
    # RefinedQuery → function logs and degrades to returning raw_output.
    llm, calls = _make_runnable_llm([
        "I cannot help with that.",   # initial chain.invoke output
        "still not json",             # parse_llm_response retry
    ])

    result = qca.refine_query_with_history(
        history=[],
        latest_query="???",
        llm=llm,
    )

    # Legacy fallback: function returns the raw_output string on
    # unrecoverable failure (parsers.py path already returned a Failure
    # envelope; this function downgrades to the raw text instead of
    # crashing — see Query_Classification_And_Analysis.py:511-518).
    assert isinstance(result, str)
    assert len(calls) == 2                # chain + 1 retry
    assert log_error_calls, "expected failure to be logged"


# ===========================================================================
# classify_query_multilabel
# ===========================================================================

def test_classify_query_multilabel_fallback_category_shortcut(
    monkeypatch, log_error_calls
):
    """Happy path that ALSO avoids the deep decompose-sub-queries chain.

    If the LLM returns a FALLBACK category (e.g. 'Negatively Intended
    Query'), the function short-circuits at line 2502-2510 and returns
    immediately — without invoking the secondary
    decompose_multi_intent_query_into_sub_queries chain. Keeps the test
    tight while still exercising the happy-path branch of P1-5 wiring."""

    # Stub Redis so we don't hit it.
    monkeypatch.setattr(qca, "get_chat", lambda key: [])

    llm, calls = _make_runnable_llm([
        '{"categories": ["Negatively Intended Query"]}'
    ])

    result = qca.classify_query_multilabel(
        user_query="this question is nonsense",
        llm=llm,
        chatId="test-chat-id",
    )

    assert isinstance(result, dict)
    assert result["classified_intents"] == ["Negatively Intended Query"]
    assert "Negatively Intended Query" in result["sub_queries"]
    assert log_error_calls == []
    assert len(calls) == 1                # chain only — no retry, no decompose


def test_classify_query_multilabel_failure_returns_other_industry(
    monkeypatch, log_error_calls
):
    """Both attempts return garbage → parse_llm_response returns a
    Failure envelope → safe_parse_output salvage also fails → function
    falls through to the 'Other industry-related queries' default at
    lines 2519-2523."""

    monkeypatch.setattr(qca, "get_chat", lambda key: [])

    llm, calls = _make_runnable_llm([
        "I cannot answer this.",   # chain.invoke
        "still nonsense",          # parse_llm_response retry
    ])

    result = qca.classify_query_multilabel(
        user_query="???",
        llm=llm,
        chatId="test-chat-id",
    )

    assert isinstance(result, dict)
    assert result["classified_intents"] == ["Other industry-related queries"]
    assert result["sub_queries"]["Other industry-related queries"] == "???"
    assert log_error_calls, "expected failure to be logged"
    assert len(calls) == 2                # chain + 1 retry
