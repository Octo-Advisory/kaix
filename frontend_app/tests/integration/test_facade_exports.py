"""FaÃ§ade guard for the QCA P2-1a split.

Asserts that the public names the rest of the app imports from
Query_Classification_And_Analysis are STILL importable from it after
each extraction step. Protects the 5 `import *` consumers
(AI.py, helper_ai_for_agents.py, incentive/vendor/approval/build_from_scratch).
"""
from frontend_app.Ai_module import Query_Classification_And_Analysis as qca


PUBLIC_NAMES = [
    "classify_query",
    "refine_query_with_history",
    "parse_llm_response",
    "respond_to_negative_query",
    "extract_location_from_query",
    "extract_comparison_locations",
    "llm_70b_vers",
    "llm_70b_vers_creative",
    "LOCATION_NOT_AVAILABLE_MSG",
# --- newly extracted into parsers.py (P2-1a, step parsers) ---
    "extract_json_object",
    "safe_parse_output",
    "extract_json_from_llm_response",
    "convert_string_json",
]


def test_public_names_still_exported():
    missing = [name for name in PUBLIC_NAMES if not hasattr(qca, name)]
    assert not missing, f"QCA faÃ§ade lost these names: {missing}"