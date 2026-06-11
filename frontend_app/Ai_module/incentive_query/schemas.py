"""Pydantic boundary schemas for the incentive-query LLM outputs.

Source LLM call: Ai_module/incentive_query/Extraction_for_incentive_search.py
  - classify_incentive_query()
    Prompt: 'Return ONLY the classification number: 1, 2, 3, 4, or 5.'
    Parser: re.search(r"^\s*([1-5])\s*$", ...) -> IncentiveClassification.
    On parse/validation miss: one corrective retry, then returns an
    IncentiveClassificationFailure envelope (no exception raised).

Category mapping (lines 115-121):
    1 — Incentive Search for area, city, or state without industry
    2 — Incentive Search for industry without location
    3 — Incentive Search for area, city, or state with industry
    4 — Other Intent
    5 — Negatively Intended Query
"""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


IncentiveCategoryNumber = Literal[1, 2, 3, 4, 5]


class IncentiveClassification(BaseModel):
    """Happy path: integer 1-5."""
    model_config = ConfigDict(extra="ignore")

    classification_number: IncentiveCategoryNumber


class IncentiveClassificationFailure(BaseModel):
    """Typed envelope returned when classification cannot be recovered.
    Covers:
      - Digit out of range (0, 6, 999)
      - Word instead of digit ("two", "five")
      - Multi-token output ("1, 3" or "1 and 3")
      - LLM ignoring 'no text' instruction and returning prose
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    classification_number: Optional[int] = None