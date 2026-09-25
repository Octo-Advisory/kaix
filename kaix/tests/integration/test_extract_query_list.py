"""Integration test for Management_Class.helpers.utility.extract_query_list.

End-to-end exercise of the P1-5 wiring:
    generate_query_hints (stubbed)
        → parse_llm_response
            → llm_70b_vers_creative (stubbed via FakeLLM, used only on retry)
                → returns QueryHintList OR QueryHintListFailure

Happy path  : the stubbed promreturns list[dict].
    generate_query_hints (stubbed)
        → parse_llm_response
            → llm_70b_vers_creused only on retry)
                → returns QueryHintList OR QueryHintListFailure

Happy path  : the stubbed prompt response is valid JSON → returns list[dict].
Failure path: the stubbed promthe retry LLM is
              also garbage → returns a QueryHintListFailure envelope, no
              exception leaks,at least once.

Stub points:
  utility.generate_query_hints  ← replaced with a lambda returning canned raw
  utility.llm_70b_vers_creativfor the retry
"""

from kaix.Management_Class.helpers import utility
from kaix.Ai_module.query_hints.schemas import QueryHintListFailure


# ---------------------------------------------------------------------------
# Happy path — valid JSON on first attempt, no retry needed
# ---------------------------------------------------------------------------

def test_extract_query_list_happy_returns_list_of_dicts(
    monkeypatch, log_error_calls
):
    valid_raw = (
        '{"hints": ['
        '{"query": "Where can I set up textile?", "module": "Build from Scratch"},'
        '{"query": "Vendors for cotton in Battambang?", "module": "Vendor Search"}'
        ']}'
    )
    # Stub generate_query_hints so no real LLM call is made for the
    # initial prompt. parse_llm_response will succeed on its first parse
    # of valid_raw, so the retry client is never invoked.
    monkeypatch.setattr(
        utility, "generate_query_hints",
        lambda query_list, input_industry_name: valid_raw,
    )

    result = utility.extract_query_list(
        query_list=["where to set up textile"],
        input_industry_name="textile",
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["query"].startswith("Where can")
    assert result[0]["module"] == "Build from Scratch"
    assert result[1]["module"] == "Vendor Search"
    # No failures => frappe.log_error must NOT have been called.
    assert log_error_calls == []


# ---------------------------------------------------------------------------
# Failure path — both the prompt response AND the retry are garbage
# ---------------------------------------------------------------------------

def test_extract_query_list_failure_returns_typed_envelope(
    monkeypatch, log_error_calls, fake_llm
):
    # Plain prose, no JSON, no bracket-list pattern — guarantees the
    # ast.literal_eval salvage regex at line 580 also misses, forcing the
    # function down the failure-envelope branch.
    monkeypatch.setattr(
        utility, "generate_query_hints",
        lambda query_list, input_industry_name: "I cannot help with that.",
    )
    # llm_70b_vers_creative is used only inside parse_llm_response on the
    # corrective retry. Hand it ONE garbage response so the retry also fails.
    monkeypatch.setattr(
        utility, "llm_70b_vers_creative",
        fake_llm(["still nonsense"]),
    )

    result = utility.extract_query_list(
        query_list=["nonsense"],
        input_industry_name="textile",
    )

    # The contract: never an ad-hoc error string, always a typed envelope.
    assert isinstance(result, QueryHintListFailure)
    assert result.error
    # Both parse_llm_response and extract_query_list log on failure, so
    # at least one capture is guaranteed.
    assert log_error_calls, "expected at least one frappe.log_error call on failure"
