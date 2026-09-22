"""Pydantic boundary schemas for the multi-label intent classifier output.

Source LLM call: 
Ai_module/Query_Classification_And_Analysis.py
  - safe_parse_output(): validates the LLM output at the json.loads,ast.literal_eval, and bracket-scan parse sites.
  - Consumed by classify_query_multilabel() at the chain.invoke() call site,which performs the P1-5 corrective retry on IntentClassificationFailure.
  
Expected LLM output: a JSON/Python list of one or more category strings.
  
  Valid categories (9), per the MAIN_CATEGORIES + FALLBACK_CATEGORIES sets defined in both safe_parse_output() and 
  classify_query_multilabel():
  MAIN:
    "Query to build industry from Scratch"
    "Query to search Vendors"
    "Query to search Incentives"
    "Query to Get Approvals"
    "Query to Get Employee Search"
  FALLBACK:
    "Negatively Intended Query"
    "Other industry-related queries"
    "Valueless queries"
    "Follow-up Query"
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


IntentCategory = Literal[
    "Query to build industry from Scratch",
    "Query to search Vendors",
    "Query to search Incentives",
    "Query to Get Approvals",
    "Query to Get Employee Search",
    "Negatively Intended Query",
    "Other industry-related queries",
    "Valueless queries",
    "Follow-up Query",
]


class IntentClassification(BaseModel):
    """Happy path: non-empty list of known category strings.

    Covers silent failure shapes:
      #1 single string instead of list  — schema requires List
      #2 unknown category string        — Literal rejects
      #3 mixed types e.g. [1, "..."]   — Literal[str] rejects ints
      #4 empty list                     — min_length=1 rejects
    """
    model_config = ConfigDict(extra="ignore")

    categories: List[IntentCategory] = Field(..., min_length=1)

    @field_validator("categories")
    @classmethod
    def no_duplicates(cls, v: List[str]) -> List[str]:
        seen = []
        for c in v:
            if c not in seen:
                seen.append(c)
        return seen


class IntentClassificationFailure(BaseModel):
    """Typed envelope. Covers:
      - Markdown-fenced output (json.loads + ast.literal_eval both fail)
      - Empty list after dedup
      - Unknown category strings
      - Mixed-type contents

    Callers MUST check this shape before iterating categories — previously
    safe_parse_output() returned [] silently in all these cases, making
    downstream routing failures impossible to debug.
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    categories: Optional[List[str]] = None  # loose — preserves garbage for logs