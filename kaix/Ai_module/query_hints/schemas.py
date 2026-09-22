"""Pydantic boundary schemas for the query-hints LLM output.

Source LLM call: Management_Class/helpers/utility.py
  - generate_query_hints()  builds the prompt
  - extract_query_list()    lines 546-554 parses via ast.literal_eval

Expected LLM output (from the prompt's FINAL OUTPUT FORMAT section):
    [
       {"query": "<generated_question_1>", "module": "<classified_module>"},
       ...
    ]

Valid module values (5) from MODULE DEFINITIONS section:
    Build from Scratch | Employment | Vendor Search | Incentives | Approval
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


ModuleName = Literal[
    "Build from Scratch",
    "Employment",
    "Vendor Search",
    "Incentives",
    "Approval",
]


class QueryHint(BaseModel):
    """One generated follow-up question + its classified module.
    Happy path: both fields present, non-empty, module is one of 5 known names."""
    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1)
    module: ModuleName

    @field_validator("query")
    @classmethod
    def query_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query is empty or whitespace-only")
        return v


class QueryHintList(BaseModel):
    """Wrapper enforcing list-of-dicts shape.
    Covers silent failure #2: LLM returns a single dict instead of a list."""
    model_config = ConfigDict(extra="ignore")

    hints: List[QueryHint] = Field(..., min_length=1)


class QueryHintListFailure(BaseModel):
    """Typed envelope when ast.literal_eval succeeds shape-wise but pydantic
    rejects the contents, OR when ast.literal_eval itself fails (markdown
    fences, single dict, None values, unknown module names)."""
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    hints: Optional[List["QueryHintLoose"]] = None


class QueryHintLoose(BaseModel):
    """Best-effort recovery shape — every field optional.
    Used inside QueryHintListFailure.hints so the caller can still salvage
    partially valid rows (e.g. row 3 had a bad module but rows 1,2 are fine)."""
    model_config = ConfigDict(extra="ignore")

    query: Optional[str] = None
    module: Optional[str] = None  # NOT Literal — accepts garbage for debugging


QueryHintListFailure.model_rebuild()