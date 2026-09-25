"""Pydantic boundary schemas for the build-from-scratch LLM outputs.

Source LLM calls: Ai_module/build_from_scratch/Extraction_for_Building_from_Scratch.py
  1) classify_industry_setup_query()       lines 15-253
     Output: integer 1-6 (regex r"^\s*([1-6])\s*$").
  2) extract_locations_from_query_multi()  lines 256-466
     Output JSON: {"Locations": [{"Location": "..."}, ...]}
     Current parser _safe_json_extract() at line 437 returns
     {"Locations": []} silently on any failure (fence-wrapped output,
     malformed JSON, plain prose).
  3) get_ai_recommended_states()           lines 750-764
     Output JSON: {"states": ["State1", ...]}
  4) get_ai_recommended_districts()        lines 847-861
     Output JSON: {"districts": ["District1", ...]}
  5) extract_json_main_industry_details()  lines 935-1024
     Output JSON: {"Main-Industry": ..., "Original-Inferred-Main-Industry": ...,
                   "Forced-Mapping": "Yes"|"No", "Product": ...}
     Reused by: extract_main_industry_and_product_for_scratch() line 1162
  6) extract_json_sub_sector_product()     lines 1171-1258
     Output JSON: {"Sub-Sector": ..., "Original-Inferred-Sub-Sector": ...,
                   "Forced-Mapping": "Yes"|"No", "Product": ...}
     Reused by: extract_sub_sector_and_product_for_scratch() line 1444
  7) extract_json_segment_and_product()    lines 1453-1540
     Output JSON: {"Segment": ..., "Original-Inferred-Segment": ...,
                   "Forced-Mapping": "Yes"|"No", "Product": ...}
     Reused by: extract_segment_and_product_for_scratch() line 1728
  8) extract_json_capacity_details()       lines 1737-1835
     Output JSON: {"Capacity": float|"None", "Capacity Unit": ..., "Time Period": ...}
     Reused by: extract_capacity_details() line 1939
  9) extract_json_time_conversion()        lines 3084-3155
     Output JSON: {"Multiplier": <float>}
     Reused by: time_conversion() line 3325
 10) extract_json_unit_conversion()        lines 3157-3235
     Output JSON: {"Multiplier": <float>}
     Reused by: unit_conversion() line 3411
 11) extract_json_unit_split()             lines 3445-3469
     Output JSON: {"unit": ..., "time_period": ...}
     Reused by: split_unit_and_time_period() line 3638

Build-from-scratch classification mapping (lines 39-46):
    1 — Intent to Build Industry from Scratch
    2 — Intent to Acquire Existing Industrial Infrastructure
    3 — Intent to Set Up Industry with Unspecified Build or Buy Intent
    4 — Other Intent
    5 — Negatively Intended Query
    6 — Intent to Evaluate Both Building from Scratch and Acquiring
        Existing Infrastructure
"""

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# 1. classify_industry_setup_query
# ---------------------------------------------------------------------------

BuildSetupCategoryNumber = Literal[1, 2, 3, 4, 5, 6]


class BuildSetupClassification(BaseModel):
    """Happy path: integer 1-6."""
    model_config = ConfigDict(extra="ignore")

    classification_number: BuildSetupCategoryNumber


class BuildSetupClassificationFailure(BaseModel):
    """Typed envelope (replaces ValueError at line 253)."""
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    classification_number: Optional[int] = None


# ---------------------------------------------------------------------------
# 2. extract_locations_from_query_multi
# ---------------------------------------------------------------------------

class LocationEntry(BaseModel):
    """One extracted location string. The prompt promises
    {'Location': '<verbatim user text>'} — preserve verbatim
    casing/abbreviations (see prompt rule 6, lines 318-340).
    """
    model_config = ConfigDict(extra="ignore")

    Location: str = Field(..., min_length=1)

    @field_validator("Location")
    @classmethod
    def reject_blank_or_none_string(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Location is whitespace-only")
        if stripped.lower() == "none":
            raise ValueError("Location is the literal sentinel 'None'")
        return stripped


class BuildLocationsExtraction(BaseModel):
    """Happy path output of extract_locations_from_query_multi."""
    model_config = ConfigDict(extra="ignore")

    Locations: List[LocationEntry] = Field(default_factory=list)

    @field_validator("Locations", mode="before")
    @classmethod
    def coerce_string_items_to_dicts(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError(
                f"Locations must be a list, got {type(v).__name__}"
            )
        coerced = []
        for item in v:
            if isinstance(item, str):
                coerced.append({"Location": item})
            elif isinstance(item, dict):
                coerced.append(item)
            else:
                raise ValueError(
                    f"Locations items must be str or dict, "
                    f"got {type(item).__name__}"
                )
        return coerced


class BuildLocationsExtractionFailure(BaseModel):
    """Typed envelope. Replaces the silent {'Locations': []} fallback at
    line 445 — callers can now distinguish 'no locations mentioned'
    (happy path with empty list) from 'parser failed' (this envelope).
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    Locations: Optional[List[dict]] = None


# ---------------------------------------------------------------------------
# 3. get_ai_recommended_states
# ---------------------------------------------------------------------------

class AIRecommendedStates(BaseModel):
    """Happy path output of get_ai_recommended_states.
    Returns 0..25 official Cambodian province names (khett) in AI ranking order.
    Open list — no literal restriction (prompt does not enumerate).
    """
    model_config = ConfigDict(extra="ignore")

    states: List[str] = Field(default_factory=list)

    @field_validator("states", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise ValueError(
                f"'states' must be a list, got {type(v).__name__}"
            )
        return v

    @field_validator("states")
    @classmethod
    def clean_dedupe(cls, v: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for s in v:
            if not isinstance(s, str):
                raise ValueError(
                    f"state entries must be str, got {type(s).__name__}"
                )
            cleaned = s.strip()
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            out.append(cleaned)
        return out


class AIRecommendedStatesFailure(BaseModel):
    """Typed envelope. Replaces the silent `ai_states = []` fallback at
    line 764 so callers can distinguish 'AI returned no states' from
    'parser failed'.
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    states: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# 4. get_ai_recommended_districts
# ---------------------------------------------------------------------------

class AIRecommendedDistricts(BaseModel):
    """Happy path output of get_ai_recommended_districts.
    Returns 0..25 official district names within the requested state,
    in AI ranking order. Open list — no literal restriction.
    """
    model_config = ConfigDict(extra="ignore")

    districts: List[str] = Field(default_factory=list)

    @field_validator("districts", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise ValueError(
                f"'districts' must be a list, got {type(v).__name__}"
            )
        return v

    @field_validator("districts")
    @classmethod
    def clean_dedupe(cls, v: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for s in v:
            if not isinstance(s, str):
                raise ValueError(
                    f"district entries must be str, got {type(s).__name__}"
                )
            cleaned = s.strip()
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            out.append(cleaned)
        return out


class AIRecommendedDistrictsFailure(BaseModel):
    """Typed envelope. Replaces the silent `ai_districts = []` fallback
    at line 861.
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    districts: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# 5. extract_json_main_industry_details
#    Reused by: extract_main_industry_and_product_for_scratch (line 1162)
# ---------------------------------------------------------------------------

class MainIndustryExtraction(BaseModel):
    """Happy path output of extract_json_main_industry_details
    (and its only orchestrator, extract_main_industry_and_product_for_scratch).
    Hyphenated keys are aliased; populate_by_name allows attribute access.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    main_industry: str = Field(..., alias="Main-Industry")
    original_inferred_main_industry: str = Field(
        ..., alias="Original-Inferred-Main-Industry"
    )
    forced_mapping: Literal["Yes", "No"] = Field(..., alias="Forced-Mapping")
    product: str = Field(..., alias="Product")

    @field_validator(
        "main_industry",
        "original_inferred_main_industry",
        "product",
    )
    @classmethod
    def reject_blank(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("field is empty/whitespace")
        return v.strip()


class MainIndustryExtractionFailure(BaseModel):
    """Typed envelope. Replaces the silent default-dict fallback in the
    helper (lines 1010-1024) so callers can distinguish a well-formed
    LLM output containing 'None' sentinels from a malformed/missing output.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    error: str
    raw_output: str
    main_industry: Optional[str] = Field(None, alias="Main-Industry")
    original_inferred_main_industry: Optional[str] = Field(
        None, alias="Original-Inferred-Main-Industry"
    )
    forced_mapping: Optional[str] = Field(None, alias="Forced-Mapping")
    product: Optional[str] = Field(None, alias="Product")


# ---------------------------------------------------------------------------
# 6. extract_json_sub_sector_product
#    Reused by: extract_sub_sector_and_product_for_scratch (line 1444)
# ---------------------------------------------------------------------------

class SubSectorExtraction(BaseModel):
    """Happy path output of extract_json_sub_sector_product
    (and its only orchestrator, extract_sub_sector_and_product_for_scratch).
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    sub_sector: str = Field(..., alias="Sub-Sector")
    original_inferred_sub_sector: str = Field(
        ..., alias="Original-Inferred-Sub-Sector"
    )
    forced_mapping: Literal["Yes", "No"] = Field(..., alias="Forced-Mapping")
    product: str = Field(..., alias="Product")

    @field_validator(
        "sub_sector",
        "original_inferred_sub_sector",
        "product",
    )
    @classmethod
    def reject_blank(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("field is empty/whitespace")
        return v.strip()


class SubSectorExtractionFailure(BaseModel):
    """Typed envelope. Replaces the silent default-dict fallback at
    lines 1245-1258.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    error: str
    raw_output: str
    sub_sector: Optional[str] = Field(None, alias="Sub-Sector")
    original_inferred_sub_sector: Optional[str] = Field(
        None, alias="Original-Inferred-Sub-Sector"
    )
    forced_mapping: Optional[str] = Field(None, alias="Forced-Mapping")
    product: Optional[str] = Field(None, alias="Product")


# ---------------------------------------------------------------------------
# 7. extract_json_segment_and_product
#    Reused by: extract_segment_and_product_for_scratch (line 1728)
# ---------------------------------------------------------------------------

class SegmentExtraction(BaseModel):
    """Happy path output of extract_json_segment_and_product
    (and its only orchestrator, extract_segment_and_product_for_scratch).
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    segment: str = Field(..., alias="Segment")
    original_inferred_segment: str = Field(
        ..., alias="Original-Inferred-Segment"
    )
    forced_mapping: Literal["Yes", "No"] = Field(..., alias="Forced-Mapping")
    product: str = Field(..., alias="Product")

    @field_validator(
        "segment",
        "original_inferred_segment",
        "product",
    )
    @classmethod
    def reject_blank(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("field is empty/whitespace")
        return v.strip()


class SegmentExtractionFailure(BaseModel):
    """Typed envelope. Replaces the silent default-dict fallback at
    lines 1526-1540.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    error: str
    raw_output: str
    segment: Optional[str] = Field(None, alias="Segment")
    original_inferred_segment: Optional[str] = Field(
        None, alias="Original-Inferred-Segment"
    )
    forced_mapping: Optional[str] = Field(None, alias="Forced-Mapping")
    product: Optional[str] = Field(None, alias="Product")


# ---------------------------------------------------------------------------
# 8. extract_json_capacity_details
#    Reused by: extract_capacity_details (line 1939)
# ---------------------------------------------------------------------------

class CapacityExtraction(BaseModel):
    """Happy path output of extract_json_capacity_details
    (and its only orchestrator, extract_capacity_details).
    Capacity is float in the happy case; the literal sentinel "None"
    is also accepted because the prompt and normalize_number both allow it.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    capacity: Union[float, Literal["None"]] = Field(..., alias="Capacity")
    capacity_unit: str = Field(..., alias="Capacity Unit")
    time_period: str = Field(..., alias="Time Period")

    @field_validator("capacity", mode="before")
    @classmethod
    def coerce_capacity(cls, v):
        # Mirrors normalize_number() (line 1756): accept int/float as-is,
        # strip commas/whitespace from strings, fall through to "None"
        # sentinel if non-numeric and not already the sentinel.
        if v is None:
            return "None"
        if isinstance(v, bool):
            raise ValueError("Capacity cannot be a bool")
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            stripped = v.replace(",", "").strip()
            if stripped == "" or stripped == "None":
                return "None"
            try:
                return float(stripped)
            except ValueError:
                return "None"
        raise ValueError(f"Capacity has unsupported type {type(v).__name__}")

    @field_validator("capacity_unit", "time_period")
    @classmethod
    def reject_blank(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("field is empty/whitespace")
        return v.strip()


class CapacityExtractionFailure(BaseModel):
    """Typed envelope. Replaces the silent default-dict fallback at
    lines 1827-1835.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    error: str
    raw_output: str
    capacity: Optional[Union[float, str]] = Field(None, alias="Capacity")
    capacity_unit: Optional[str] = Field(None, alias="Capacity Unit")
    time_period: Optional[str] = Field(None, alias="Time Period")


# ---------------------------------------------------------------------------
# 9 & 10. extract_json_time_conversion / extract_json_unit_conversion
#         Reused by: time_conversion (line 3325), unit_conversion (line 3411)
# ---------------------------------------------------------------------------

class MultiplierResult(BaseModel):
    """Happy path output for both extract_json_time_conversion and
    extract_json_unit_conversion (and their orchestrators time_conversion
    / unit_conversion). Both prompts ask for the identical shape
    {"Multiplier": <conversion_multiplier>}.
    """
    model_config = ConfigDict(extra="ignore")

    Multiplier: float

    @field_validator("Multiplier", mode="before")
    @classmethod
    def coerce_to_float(cls, v):
        # Both helpers float() their input; tolerate ints, numeric strings,
        # and reject booleans/empty values at the boundary.
        if v is None:
            raise ValueError("Multiplier is null")
        if isinstance(v, bool):
            raise ValueError("Multiplier cannot be a bool")
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("Multiplier is empty string")
            try:
                return float(stripped)
            except ValueError as e:
                raise ValueError(f"Multiplier not numeric: {stripped!r}") from e
        raise ValueError(
            f"Multiplier has unsupported type {type(v).__name__}"
        )


class MultiplierResultFailure(BaseModel):
    """Typed envelope. Replaces the silent `{"Multiplier": 1.0}` fallback
    at lines 3155 / 3235 so callers can distinguish 'LLM said 1.0' from
    'parser fell back to 1.0' (which would silently no-op the conversion).
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    Multiplier: Optional[float] = None


# ---------------------------------------------------------------------------
# 11. extract_json_unit_split
#     Reused by: split_unit_and_time_period (line 3638)
# ---------------------------------------------------------------------------

UnitTimePeriod = Literal[
    "per annum",
    "per day",
    "per hour",
    "per month",
    "per week",
    "per minute",
    "per second",
    "per shift",
    "per batch",
]


class UnitTimeSplit(BaseModel):
    """Happy path output of extract_json_unit_split
    (and its only orchestrator, split_unit_and_time_period).
    The current code raises ValueError at line 3469 on any miss —
    this schema preserves that strictness for the happy path.
    """
    model_config = ConfigDict(extra="ignore")

    unit: str = Field(..., min_length=1)
    time_period: UnitTimePeriod

    @field_validator("unit")
    @classmethod
    def reject_blank_unit(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f"unit must be str, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("unit is whitespace-only")
        # Preserve verbatim casing/spacing per prompt rule 1 (line 3490);
        # only outer whitespace is stripped.
        return stripped


class UnitTimeSplitFailure(BaseModel):
    """Typed envelope. Replaces the ValueError raised at line 3469
    so callers of split_unit_and_time_period can branch on a typed
    failure instead of an exception that currently crashes the chain.
    """
    model_config = ConfigDict(extra="ignore")

    error: str
    raw_output: str
    unit: Optional[str] = None
    time_period: Optional[str] = None