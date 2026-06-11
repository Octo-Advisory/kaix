"""Pydantic boundary schemas for the approval-query LLM outputs.

Source LLM call: Ai_module/approval_query/Extraction_for_approval_search.py
  - classify_approval_query()  lines 82-209
    Prompt instructs: "return ONLY the classification number (1, 2, 3, 4, or 5)".
    Current parser: re.search(r"^\s*([1-5])\s*$", response.content.strip())
    Raises ValueError on mismatch — no typed envelope today.

Category mapping (lines 106-112):
    1 — Approval Search for area, city, or state without industry
    2 — Approval Search for industry without location
    3 — Approval Search for area, city, or state with industry
    4 — Other Intent
    5 — Negatively Intended Query
"""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


ApprovalCategoryNumber = Literal[1, 2, 3, 4, 5]

ApprovalCategoryLabel = Literal[
    "Approval Search for area, city, or state without industry",
    "Approval Search for industry without location",
    "Approval Search for area, city, or state with industry",
    "Other Intent",
    "Negatively Intended Query",
]


class ApprovalClassification(BaseModel):
    """Happy path: a single integer 1-5.

    Failure shapes this rejects:
      - LLM returns a word ("two") instead of a digit
      - LLM returns out-of-range number (0, 6, 999)
      - LLM returns multiple digits ("1, 3")
      - LLM returns prose explaining the digit
    """
    model_config = ConfigDict(extra="ignore")

    classification_number: ApprovalCategoryNumber


class ApprovalClassificationFailure(BaseModel):
    """Typed envelope replacing the current ValueError raise.

    Caller can decide between retry, fallback to negative-intent path,
    or surface a 'sorry I didn't catch that' to the user.
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    classification_number: Optional[int] = None  # loose for forensics