r"""Pydantic boundary schema for the chat-history query-refinement output.

Source LLM call: Ai_module/Query_Classification_And_Analysis.py
  - refine_query_with_history()  ~ line 107 / parses at 492-506
  - Plus the per-module copies:
      approval_query    line 31 (refine_query_with_history_for_approval)
      vendor_query      line 35 (refine_query_with_history_for_vendor)
      incentive_query   line 34 (refine_query_with_history_for_incentive)
      employement_query line 37 (refine_query_with_history_for_employment)

Expected LLM output (from OUTPUT REQUIREMENTS section of the prompt,
line 441 onward):
    A single standalone reformulated query as a plain string.
    No JSON, no list — just text.

The current parser extracts via:
    r'reformulated standalone query:\s*(?:"(.*?)|\'(.*?)\'|(.*))$'
with fallback to the entire response if no match. Failure shapes
include: empty string, multi-line output, prompt echo, or the LLM
emitting JSON when text was requested.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RefinedQuery(BaseModel):
    """Happy path: single non-empty single-line refined query string."""
    model_config = ConfigDict(extra="ignore")

    refined_query: str = Field(..., min_length=1, max_length=2000)

    @field_validator("refined_query")
    @classmethod
    def must_be_clean_text(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("refined_query is empty after strip")

        lowered = stripped.lower()

        if lowered.startswith("reformulated standalone query:"):
            raise ValueError("refined_query still contains the prompt label")

        if lowered.startswith("output:") or lowered.startswith("input:"):
            raise ValueError("refined_query starts with a prompt header")

        # Rejects multi-paragraph reasoning blobs
        if "\n\n" in stripped:
            raise ValueError(
                "refined_query contains a paragraph break (multi-paragraph output)"
            )

        return stripped


class RefinedQueryFailure(BaseModel):
    """Typed envelope. Covers:
      - LLM returned an empty string
      - LLM echoed the prompt label
      - LLM returned multi-paragraph reasoning instead of a single query
      - Regex match in the legacy parser captured the wrong group
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    refined_query: Optional[str] = None