"""Unit tests for Ai_module/parsers.py::parse_llm_response.

Covers the retry-once-and-return-envelope contract:
- happy path returns a model instance
- extra keys are ignored
- invalid JSON triggers retry
- validation error triggers retry
- both attempts failing returns a typed failure envelope
- failure envelope falls back to plain dict when no sibling class exists
- LLM .invoke() raising on retry is caught
- frappe.log_error is called once on final failure with the stable title

No network, no DB writes — uses the FakeLLM and log_error_calls fixtures
from conftest.py.
"""

from pydantic import BaseModel, ConfigDict

from kaix.Ai_module.parsers import parse_llm_response


# ---------------------------------------------------------------------------
# Local test models — defined HERE so this module is the home module that
# _resolve_failure_envelope searches via sys.modules for sibling Failure
# classes. WidgetModel has a sibling; OrphanModel deliberately does not.
# ---------------------------------------------------------------------------

class WidgetModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    count: int


class WidgetModelFailure(BaseModel):
    """Sibling envelope contract from parsers.py: 'error' and 'raw_output'."""
    model_config = ConfigDict(extra="ignore")
    error: str
    raw_output: str


class OrphanModel(BaseModel):
    """No sibling OrphanModelFailure — exercises the dict fallback branch."""
    model_config = ConfigDict(extra="ignore")
    value: str


# ---------------------------------------------------------------------------
# 1. Happy path — valid JSON, no retry
# ---------------------------------------------------------------------------

def test_happy_path_returns_model_instance(fake_llm):
    llm = fake_llm([])  # no canned responses — first parse must succeed
    raw = '{"name": "gear", "count": 3}'

    result = parse_llm_response(
        raw=raw, model_class=WidgetModel, llm_client=llm, prompt="p"
    )

    assert isinstance(result, WidgetModel)
    assert result.name == "gear"
    assert result.count == 3
    assert llm.call_count == 0


# ---------------------------------------------------------------------------
# 2. Extra keys are ignored (ConfigDict extra="ignore")
# ---------------------------------------------------------------------------

def test_extra_keys_ignored(fake_llm):
    llm = fake_llm([])
    raw = '{"name": "gear", "count": 3, "stray": "ignored"}'

    result = parse_llm_response(
        raw=raw, model_class=WidgetModel, llm_client=llm, prompt="p"
    )

    assert isinstance(result, WidgetModel)
    assert llm.call_count == 0


# ---------------------------------------------------------------------------
# 3. Invalid JSON → retry succeeds
# ---------------------------------------------------------------------------

def test_invalid_json_triggers_retry_which_succeeds(fake_llm):
    good = '{"name": "gear", "count": 3}'
    llm = fake_llm([good])

    result = parse_llm_response(
        raw="not json at all",
        model_class=WidgetModel,
        llm_client=llm,
        prompt="p",
    )

    assert isinstance(result, WidgetModel)
    assert llm.call_count == 1
    # Retry MUST request JSON-object mode so the LLM cannot return prose.
    _prompt, kwargs = llm.calls[0]
    assert kwargs.get("response_format") == {"type": "json_object"}


# ---------------------------------------------------------------------------
# 4. Schema mismatch → retry succeeds
# ---------------------------------------------------------------------------

def test_validation_error_triggers_retry_which_succeeds(fake_llm):
    good = '{"name": "gear", "count": 3}'
    llm = fake_llm([good])
    bad = '{"name": "gear", "count": "not-an-int"}'  # valid JSON, bad schema

    result = parse_llm_response(
        raw=bad, model_class=WidgetModel, llm_client=llm, prompt="p"
    )

    assert isinstance(result, WidgetModel)
    assert llm.call_count == 1


# ---------------------------------------------------------------------------
# 5. Both attempts fail → typed failure envelope (sibling exists)
# ---------------------------------------------------------------------------

def test_both_attempts_fail_returns_failure_envelope(fake_llm, log_error_calls):
    llm = fake_llm(["still not json"])  # retry response also bad

    result = parse_llm_response(
        raw="garbage", model_class=WidgetModel, llm_client=llm, prompt="p"
    )

    assert isinstance(result, WidgetModelFailure)
    assert result.error
    assert result.raw_output == "still not json"
    assert len(log_error_calls) == 1


# ---------------------------------------------------------------------------
# 6. Both attempts fail, no sibling → plain dict fallback
# ---------------------------------------------------------------------------

def test_failure_falls_back_to_dict_when_no_sibling(fake_llm, log_error_calls):
    llm = fake_llm(["also bad"])

    result = parse_llm_response(
        raw="bad", model_class=OrphanModel, llm_client=llm, prompt="p"
    )

    assert isinstance(result, dict)
    assert "error" in result
    assert result["raw_output"] == "also bad"
    assert len(log_error_calls) == 1


# ---------------------------------------------------------------------------
# 7. LLM .invoke() raises on retry → caught, envelope returned
# ---------------------------------------------------------------------------

def test_llm_invoke_raises_on_retry_returns_envelope(log_error_calls):
    class ExplodingLLM:
        def __init__(self):
            self.calls = []

        def invoke(self, prompt, **kwargs):
            self.calls.append((prompt, kwargs))
            raise RuntimeError("transport down")

    llm = ExplodingLLM()

    result = parse_llm_response(
        raw="not json", model_class=WidgetModel, llm_client=llm, prompt="p"
    )

    assert isinstance(result, WidgetModelFailure)
    # When the retry call itself raises, retry_raw stays as the original raw
    # (see parsers.py:214). The envelope must still be returned, never raised.
    assert result.raw_output == "not json"
    assert "transport down" in result.error
    assert len(log_error_calls) == 1


# ---------------------------------------------------------------------------
# 8. frappe.log_error is called once with the stable title
# ---------------------------------------------------------------------------

def test_log_error_called_with_stable_title(fake_llm, log_error_calls):
    llm = fake_llm(["still bad"])

    parse_llm_response(
        raw="bad", model_class=WidgetModel, llm_client=llm, prompt="p"
    )

    assert len(log_error_calls) == 1
    _message, title = log_error_calls[0]
    # parsers.py:53 → _LOG_TITLE = "parse_llm_response". Stable title makes
    # filtering parser failures in Frappe Desk's Error Log trivial.
    assert title == "parse_llm_response"