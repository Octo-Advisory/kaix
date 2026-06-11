
"""Shared fixtures for the P1-5 Day 8 test suite.

Provides:
- FakeLLM: a stub that mimics ChatGroq's .invoke() return shape
  (object with .content) and records every prompt + kwargs received,
  so tests can assert response_format={"type":"json_object"} was passed
  on the corrective retry path inside parse_llm_response.
- log_error_calls: a fixture that monkeypatches frappe.log_error to a
  list-recorder, so tests can assert it was called without touching the
  real Error Log doctype.
- fake_llm: a factory fixture so each test can build its own FakeLLM
  with a custom list of canned responses.
"""

import pytest

@pytest.fixture(autouse=True)
def _frappe_test_context():
    """@frappe.whitelist()-decorated functions evaluate `local.flags.in_test`
    on every call (frappe/__init__.py:843). Without an initialized Frappe site,
    frappe.local has no `flags`, raising AttributeError. Provide a minimal flags
    object so the whitelist wrapper can run. frappe._dict returns None for
    missing keys, so `flags.in_test` resolves to None (falsy) and arg-type
    validation is simply skipped."""
    import frappe
    if not getattr(frappe.local, "flags", None):
        frappe.local.flags = frappe._dict()
    yield


class _FakeAIMessage:
    """Stand-in for langchain_core.messages.AIMessage.
    parse_llm_response reads .content via getattr, so this is all it needs."""

    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    """Drop-in replacement for a ChatGroq client in tests.

    Construct with a list of canned response strings; each call to
    .invoke() pops the next one and returns it wrapped in a fake
    AIMessage. Records all (prompt, kwargs) pairs for assertions.

    Raises IndexError if the test asks for more invocations than canned
    responses — that surfaces accidental extra LLM calls loudly instead
    of silently returning None.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []  # list of (prompt, kwargs) tuples

    def invoke(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        if not self._responses:
            raise IndexError(
                f"FakeLLM exhausted after {len(self.calls)} calls; "
                "test asked for more invocations than canned responses"
            )
        return _FakeAIMessage(self._responses.pop(0))

    @property
    def call_count(self) -> int:
        return len(self.calls)


@pytest.fixture
def log_error_calls(monkeypatch):
    """Monkeypatch frappe.log_error to a recorder.

    Yields the list of (message, title) tuples captured during the test.
    Use to assert that parse_llm_response logged a failure without
    polluting the real Error Log DocType.
    """
    import frappe
    calls = []
    monkeypatch.setattr(
        frappe,
        "log_error",
        lambda message, title=None: calls.append((message, title)),
    )
    yield calls


@pytest.fixture
def fake_llm():
    """Factory fixture: tests call fake_llm([...]) to build a FakeLLM
    seeded with the responses they need.

    Example:
        def test_x(fake_llm):
            llm = fake_llm(['bad json', '{"key": "value"}'])
            ...
    """
    return FakeLLM
