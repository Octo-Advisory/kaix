
"""Integration test for Management_Class.Ai_management.AI.ai_module_call.

TST-3: happy-path exercise of ai_module_call with a stubbed Groq client.

ai_module_call branches heavily; the cleanest self-contained happy path
is the `input == "NOFROMUSER"` branch (AI.py:104-123) â the user declined
a confirmation, so the function generates a fallback message via the Groq
LLM and returns immediately, without the feasibility/agent machinery.

Only the Groq client (llm_70b_vers_creative) is replaced with a stub
Runnable; the Redis read/write and the responder-consultant polish layer
are neutralised so the test is offline and deterministic. The frappe
whitelist wrapper and frappe.log_error are handled by the autouse
fixtures in conftest.py (_frappe_test_context, log_error_calls).
"""

from langchain_core.runnables import RunnableLambda

from frontend_app.Management_Class.Ai_management import AI


class _FakeMessage:
    """Stand-in for ChatGroq's AIMessage. generate_fallback_message reads
    .content (QCA.py:4330)."""
    def __init__(self, content):
        self.content = content


def _stub_groq(canned):
    """A stubbed Groq client: a Runnable matching the `prompt | llm` chain
    shape, returning a fixed AIMessage on .invoke()."""
    return RunnableLambda(lambda _input, **_kw: _FakeMessage(canned))


def test_ai_module_call_nofromuser_happy_returns_response(
    monkeypatch, log_error_calls
):
    canned = (
        "It seems the details may not fully align with your needs â "
        "could you share the correct specifics?"
    )

    # Redis read/write â no real Redis in tests.
    monkeypatch.setattr(AI, "get_chat", lambda key: [])
    monkeypatch.setattr(AI, "save_chat", lambda *a, **k: None)

    # The stubbed Groq client used by the fallback path.
    monkeypatch.setattr(AI, "llm_70b_vers_creative", _stub_groq(canned))

    # Neutralise the responder-consultant polish layer (it would otherwise
    # call RESPONDER_LLM). Passthrough returns the raw response unchanged.
    monkeypatch.setattr(
        AI, "polish_ai_response_if_possible",
        lambda raw_response, **kwargs: raw_response,
    )

    result = AI.ai_module_call(
        input="NOFROMUSER",
        confirmationMessage="Are these the details you wanted?",
        chatId="test-chat-id",
    )

    # Happy-path contract of the NOFROMUSER branch (AI.py:108-123).
    assert isinstance(result, dict)
    assert result["Ai_response"] == canned
    assert result["Is_confirmation"] is None
    assert result["Error"] is None
