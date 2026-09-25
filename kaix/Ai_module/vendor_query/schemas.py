"""Pydantic boundary schemas for the vendor-query LLM outputs.

Source LLM calls: Ai_module/vendor_query/Extraction_for_vendor_search.py
  1) classify_vendor_query()             lines 115-301
     Output: integer 1-7 (regex r"^\s*([1-7])\s*$").
  2) extract_location_from_vendor_query() lines 303-418
     Output: JSON-ish blob parsed by 3 separate regexes (lines 404-406):
       {"Extracted_Location": "...", "Classification": "...", "From_Cambodia": "..."}
     Silently defaults Classification to "Area" and From_Cambodia to "No" on miss.
  3) extract_supplies_from_query()       lines 467-570
     Output: {"Supplies": "comma,separated,string"} parsed by one regex
     (line 551) — empty string is silently treated as "no supplies".

Vendor classification mapping (lines 143-151):
    1-5 = Vendor Search variants; 6 = Other Intent; 7 = Negatively Intended Query

Location classification values (from prompt rules 4-5, lines 344-356):
    Area | City | State | Country | None
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


VendorCategoryNumber = Literal[1, 2, 3, 4, 5, 6, 7]
LocationClass = Literal["Area", "City", "State", "Country", "None"]
FromCambodiaFlag = Literal["Yes", "No"]


class VendorClassification(BaseModel):
    """Happy path: vendor intent class 1-7."""
    model_config = ConfigDict(extra="ignore")

    classification_number: VendorCategoryNumber


class VendorClassificationFailure(BaseModel):
    """Typed envelope (replaces ValueError at line 301)."""
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    classification_number: Optional[int] = None


class VendorLocationExtraction(BaseModel):
    """Happy path output of extract_location_from_vendor_query.

    Catches the silent-defaults bug at lines 410-411:
      - "Classification" missing → currently defaults to 'Area' silently
      - "From_Cambodia" missing     → currently defaults to 'No' silently
    Schema makes both required so a missing field becomes a failure envelope
    instead of a wrong-but-plausible answer.
    """
    model_config = ConfigDict(extra="ignore")

    Extracted_Location: str = Field(..., min_length=1)
    Classification: LocationClass
    From_Cambodia: FromCambodiaFlag

    @field_validator("Extracted_Location")
    @classmethod
    def location_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Extracted_Location is whitespace-only")
        return v


class VendorLocationExtractionFailure(BaseModel):
    """Failure envelope. Covers:
      - LLM returned 'None' for location but a real Classification (inconsistency)
      - LLM returned unknown Classification value (e.g. 'Region', 'District')
      - JSON wrapped in markdown fences
      - LLM omitted From_Cambodia entirely (current code silently -> 'No')
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    Extracted_Location: Optional[str] = None
    Classification: Optional[str] = None
    From_Cambodia: Optional[str] = None


class VendorSuppliesExtraction(BaseModel):
    """Happy path output of extract_supplies_from_query.

    The LLM is asked for {'Supplies': '<Comma-Separated string or empty>'}.
    Downstream code splits the string on ',' (line 555). Schema normalises
    that to a List[str] so the parser, not every caller, handles splitting.
    """
    model_config = ConfigDict(extra="ignore")

    Supplies: List[str] = Field(default_factory=list)

    @field_validator("Supplies", mode="before")
    @classmethod
    def split_csv_if_string(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        raise ValueError(f"Supplies must be string or list, got {type(v).__name__}")


class VendorSuppliesExtractionFailure(BaseModel):
    """Failure envelope for supply extraction. Covers:
      - LLM omitted 'Supplies' key entirely
      - LLM returned non-string non-list (e.g. dict of categorised supplies)
      - JSON wrapped in markdown fences
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    Supplies: Optional[List[str]] = None