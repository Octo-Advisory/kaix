"""Integration tests for the four classify_*_query parse sites:

  classify_vendor_query     (vendor_query/Extraction_for_vendor_search.py:134)
  classify_incentive_query  (incentive_query/Extraction_for_incentive_search.py:113)
  classify_approval_query   (approval_query/Extraction_for_approval_search.py:108)
  classify_employment_query (employement_query/Extraction_for_employement_search.py:298)

All four follow the same shape:
  - chain = prompt | llm; response = chain.invoke({"query": query})
  - Regex matches a single digit → returns dict with classification_number
  - On regex miss → parse_llm_response retry → typed Failure envelope

The only variation is the valid digit range:
  vendor    1-7
  incentive 1-5
  approval  1-5
  employment 1-4

One file, 8 tests (2 per module) — same RunnableLambda pattern as
test_build_from_scratch.py."""

import pytest

@pytest.fixture(autouse=True)
def _stub_token_logging(monkeypatch):
    """update_llm_token writes to the 'Mars Config' DocType via frappe.get_doc,
    which needs a live Frappe site/DB. These tests run without one, so stub it
    to a lls it."""
    for mod in (vq, iq, aq, eq):
        monkeypatch.setattr(mod, "update_llm_token", lambda *a, **k: None, raising=False)

from langchain_core.runnables import RunnableLambda

from frontend_app.Ai_module.vendor_query import (
    Extraction_for_vendor_search as vq,
)
from frontend_app.Ai_module.vendor_query.schemas import VendorClassificationFailure

from frontend_app.Ai_module.incentive_query import (
    Extraction_for_incentive_search as iq,
)
from frontend_app.Ai_module.incentive_query.schemas import IncentiveClassificationFailure

from frontend_app.Ai_module.approval_query import (
    Extraction_for_approval_search as aq,
)
from frontend_app.Ai_module.approval_query.schemas import ApprovalClassificationFailure

from frontend_app.Ai_module.employement_query import (
    Extraction_for_employement_search as eq,
)
from frontend_app.Ai_module.employement_query.schemas import EmploymentClassificationFailure


# ---------------------------------------------------------------------------
# Helpers — shared across all 8 tests in this file
# ---------------------------------------------------------------------------

class _FakeMessage:
    """Stand-in for ChatGroq's AIMessage. .content is the only attribute
    the classify_*_query functions read directly. usage_metadata and
    response_metadata are set to safe defaults in case any of the four
    modules adds usage-logging similar to build_from_scratch."""
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        self.response_metadata = {"model": "fake-llm"}


def _runnable_llm(responses):
    """Build a RunnableLambda that pops the next canned response on
    every .invoke() call. Required because all four classify_*_query
    functions use `chain = prompt | llm` which needs a Runnable."""
    queue = list(responses)

    def _fn(input_, **kwargs):
        if not queue:
            raise IndexError(
                "fake llm exhausted — test queued too few responses"
            )
        return _FakeMessage(queue.pop(0))

    return RunnableLambda(_fn)


# ===========================================================================
# classify_vendor_query — 1-7 valid range
# ===========================================================================

def test_classify_vendor_query_happy_returns_category(log_error_calls):
    llm = _runnable_llm(["4"])  # 4 = vendor search, industry + location

    result = vq.classify_vendor_query(
        query="who supplies steel in Pune?",
        llm=llm,
    )

    assert isinstance(result, dict)
    assert result["classification_number"] == 4
    assert log_error_calls == []


def test_classify_vendor_query_failure_returns_envelope(log_error_calls):
    # 1st response: regex miss. 2nd response: parse_llm_response retry
    # also fails. End state: VendorClassificationFailure envelope.
    llm = _runnable_llm(["nine please", "still nonsense"])

    result = vq.classify_vendor_query(
        query="???",
        llm=llm,
    )

    assert isinstance(result, VendorClassificationFailure)
    assert result.error
    assert log_error_calls, "expected failure to be logged"


# ===========================================================================
# classify_incentive_query — 1-5 valid range
# ===========================================================================

def test_classify_incentive_query_happy_returns_category(log_error_calls):
    llm = _runnable_llm(["3"])  # 3 = incentive search with industry + location

    result = iq.classify_incentive_query(
        query="textile incentives in Gujarat?",
        llm=llm,
    )

    assert isinstance(result, dict)
    assert result["classification_number"] == 3
    assert log_error_calls == []


def test_classify_incentive_query_failure_returns_envelope(log_error_calls):
    llm = _runnable_llm(["I dunno", "still garbage"])

    result = iq.classify_incentive_query(
        query="???",
        llm=llm,
    )

    assert isinstance(result, IncentiveClassificationFailure)
    assert result.error
    assert log_error_calls


# ===========================================================================
# classify_approval_query — 1-5 valid range
# ===========================================================================

def test_classify_approval_query_happy_returns_category(log_error_calls):
    llm = _runnable_llm(["2"])  # 2 = approval search for industry without location

    result = aq.classify_approval_query(
        query="what approvals does a textile mill need?",
        llm=llm,
    )

    assert isinstance(result, dict)
    assert result["classification_number"] == 2
    assert log_error_calls == []


def test_classify_approval_query_failure_returns_envelope(log_error_calls):
    llm = _runnable_llm(["um", "junk again"])

    result = aq.classify_approval_query(
        query="???",
        llm=llm,
    )

    assert isinstance(result, ApprovalClassificationFailure)
    assert result.error
    assert log_error_calls


# ===========================================================================
# classify_employment_query — 1-4 valid range
# ===========================================================================

def test_classify_employment_query_happy_returns_category(log_error_calls):
    llm = _runnable_llm(["1"])  # 1 = individual employment status

    result = eq.classify_employment_query(
        query="what is unemployment in Mumbai?",
        llm=llm,
    )

    assert isinstance(result, dict)
    assert result["classification_number"] == 1
    assert log_error_calls == []


def test_classify_employment_query_failure_returns_envelope(log_error_calls):
    llm = _runnable_llm(["maybe?", "still bad"])

    result = eq.classify_employment_query(
        query="???",
        llm=llm,
    )
    assert log_error_calls == []


def test_classify_employment_query_failure_returns_envelope(log_error_calls):
    llm = _runnable_llm(["maybe?", "still bad"])

    result = eq.classify_employment_query(
        query="???",
        llm=llm,
    )

    assert isinstance(result, EmploymentClassificationFailure)
    assert result.error
    assert log_error_calls
