"""Pydantic boundary schemas for the employment-query LLM outputs.

Source LLM calls: Ai_module/employement_query/Extraction_for_employement_search.py
  1) classify_employment_query()              lines 349-505
     Output: integer 1-4 (regex r"^\s*([1-4])\s*$").
  2) extract_employment_keywords_from_query() lines 147-246 AND 248-346
     (note: the function is defined twice — the second definition wins).
     Output JSON: {"KEYWORDS": ["Skilled", "Semi-Skilled", ...] or null}
     Current parser uses extract_json_from_llm_response_employment() at
     line 83 which does json.loads -> fenced fallback -> returns
     {key: None} silently when nothing matches.

Employment classification mapping (lines 376-381):
    1 — Individual employment status
    2 — Comparison between cities, states, or areas
    3 — Other Intention
    4 — Negatively Intended Query

Skill keyword categories (prompt section 6 'FINAL OUTPUT RULES', line 217-219):
    Skilled | Semi-Skilled | Unskilled  (null when general employment)
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


EmploymentCategoryNumber = Literal[1, 2, 3, 4]
SkillLevel = Literal["Skilled", "Semi-Skilled", "Unskilled"]
UserIntent = Literal["Agree", "Disagree","Location Specific Query", "Other Intent"]


class EmploymentClassification(BaseModel):
    """Happy path: integer 1-4."""
    model_config = ConfigDict(extra="ignore")

    classification_number: EmploymentCategoryNumber


class EmploymentClassificationFailure(BaseModel):
    """Typed envelope (replaces ValueError at line 505)."""
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    classification_number: Optional[int] = None


class EmploymentKeywords(BaseModel):
    """Happy path for extract_employment_keywords_from_query.

    Prompt says output is either {'KEYWORDS': [...]} or {'KEYWORDS': null}.
    None is a meaningful sentinel for 'general employment' (no skill
    filtering) — distinct from an empty list which would mean 'LLM tried
    to classify but found nothing'. Schema preserves that distinction.

    Failure shapes rejected:
      - KEYWORDS contains a value not in {Skilled, Semi-Skilled, Unskilled}
      - KEYWORDS contains duplicates (silently passed through today)
      - KEYWORDS is a string instead of list (e.g. 'Skilled' not ['Skilled'])
    """
    model_config = ConfigDict(extra="ignore")

    KEYWORDS: Optional[List[SkillLevel]] = None

    @field_validator("KEYWORDS", mode="before")
    @classmethod
    def normalise_keywords(cls, v):
        if v is None:
            return None
        # Tolerate scalar-instead-of-list from LLM
        if isinstance(v, str):
            v = [v]
        if not isinstance(v, list):
            raise ValueError(
                f"KEYWORDS must be list or null, got {type(v).__name__}"
            )
        # Dedupe preserving order
        seen = []
        for item in v:
            if item not in seen:
                seen.append(item)
        return seen


class EmploymentKeywordsFailure(BaseModel):
    """Typed envelope. Covers the silent {key: None} fallback today emitted
    by extract_json_from_llm_response_employment() when the LLM output is
    fenced, malformed, or contains unknown skill categories.
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    KEYWORDS: Optional[List[str]] = None  # loose — accepts garbage for logs

class UserIntentClassification(BaseModel):
    """Happy path for check_user_intent.
    The prompt instructs the LLM to emit a single line of the form
    Classified intent: <One of 'Agree','Disagree','Location Specific Query','Other Intent'>
    The legacy regex silently fell back to 'Other Intent' on any miss,making genuine LLM failures indistinguishable from a real classification.
    """
    model_config = ConfigDict(extra="ignore")

    classified_intent: UserIntent


class UserIntentClassificationFailure(BaseModel):
    """Typed envelope. Covers:
    - LLM emitted no 'Classified intent:'label
    - Emitted label outside the four allowed values
    - Multi-classification output
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    classified_intent: Optional[str] = None