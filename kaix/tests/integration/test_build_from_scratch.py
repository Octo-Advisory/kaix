
"""Integration tests for parse_llm_response sites in
Ai_module/build_from_scratch/Extraction_for_Building_from_Scratch.py.

Focused scope: classify_industry_setup_query (the simplest self-contained
function in this file).

The other 10 parse sites (extract_locations_from_query_multi,
get_ai_recommended_states, get_ai_recommended_districts, the four JSON
helpers, the two conversion helpers, etc.) involve DB lookups, fuzzy
matching, and multi-step chains that don't pay back the integration-test
investment. The schema-level coverage already lives in test_schemas.py
and test_schemas_validators.py for those.

classify_industry_setup_query is a bare-int classifier that validates
directly via BuildSetupClassification (NOT via parse_llm_response — see
parsers.py:13-15: 'NOT used for bare-integer classification calls').
It still follows the typed-envelope contract on failure, so it belongs
in the Day 8 coverage set."""

from langchain_core.runnables import RunnableLambda

from kaix.Ai_module.build_from_scratch import (
    Extraction_for_Building_from_Scratch as bfs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeMessage:
    """Stand-in for ChatGroq's AIMessage with the three attributes the
    build_from_scratch code paths read:
      .content           → regex-matched for the classification digit
      .usage_metadata    → passed verbatim to the usage-logging block
      .response_metadata → looked up for .get('model')
    Only .content is validation-relevant; the other two just need to be
    dict-like so frappe.as_json at line 227-234 doesn't trip."""
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
    every .invoke() call. The function under test uses chain = prompt
    | llm, which requires a Runnable on the right side of the pipe."""
    queue = list(responses)

    def _fn(input_, **kwargs):
        if not queue:
            raise IndexError(
                "fake llm exhausted — test queued too few responses"
            )
        return _FakeMessage(queue.pop(0))

    return RunnableLambda(_fn)


# ===========================================================================
# classify_industry_setup_query — happy path
# ===========================================================================

def test_classify_industry_setup_query_happy_returns_category(log_error_calls):
    # LLM returns the digit '1' → BuildSetupClassification validates →
    # function returns the full dict including the human-readable category.
    llm = _runnable_llm(["1"])

    result = bfs.classify_industry_setup_query(
        query="I want to start a textile factory",
        llm=llm,
    )

    assert isinstance(result, dict)
    assert result["classification_number"] == 1
    assert result["classification_category"] == (
        "Intent to Build Industry from Scratch"
    )


def test_classify_industry_setup_query_happy_accepts_full_range(log_error_calls):
    # Spot-check category 6 (the highest valid digit per the Literal[1-6])
    # to defend against future "off-by-one" tweaks to BuildSetupCategoryNumber.
    llm = _runnable_llm(["6"])

    result = bfs.classify_industry_setup_query(
        query="should I build or buy?",
        llm=llm,
    )

    assert result["classification_number"] == 6


# ===========================================================================
# classify_industry_setup_query — failure paths
# ===========================================================================

def test_classify_industry_setup_query_failure_no_digit(log_error_calls):
    # LLM returns prose with no 1-6 digit → regex misses → function
    # returns BuildSetupClassificationFailure.model_dump() (P1-5 contract:
    # never a raised exception, always a typed envelope).
    llm = _runnable_llm(["I cannot answer that"])

    result = bfs.classify_industry_setup_query(
        query="???",
        llm=llm,
    )

    assert isinstance(result, dict)
    # Failure envelope keys (from BuildSetupClassificationFailure).
    assert "error" in result
    assert "raw_output" in result
    assert result.get("classification_number") is None
    assert "did not return an integer" in result["error"].lower()
    assert log_error_calls, "expected failure to be logged"


def test_classify_industry_setup_query_failure_out_of_range(log_error_calls):
    # LLM returns '7' — passes the regex (single digit) but fails the
    # Literal[1,2,3,4,5,6] schema check. Tests the ValidationError branch
    # at lines 257-263, which is distinct from the "no digit" branch above.
    #
    # NOTE: the regex r"^\s*([1-6])\s*$" rejects '7' before pydantic even
    # sees it — so this still flows through the "no match" branch. Both
    # branches return the same envelope shape, which is what matters for
    # downstream callers.
    llm = _runnable_llm(["7"])

    result = bfs.classify_industry_setup_query(
        query="???",
        llm=llm,
    )

    assert isinstance(result, dict)
    assert "error" in result
    assert result.get("classification_number") is None
    assert log_error_calls
