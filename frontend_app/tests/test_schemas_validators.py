
"""Targeted tests for non-trivial schema validators.

test_schemas.py covers one representative class per schemas.py file.
This file goes deeper into schemas with custom @field_validator logic
where future "simplifications" could silently break the parser layer.

Coverage:
  - LocationEntry          â rejects 'None' sentinel
  - BuildLocationsExtraction â coerces plain strings into dict form
  - CapacityExtraction     â coerces numeric strings,rejects bools,
                              accepts 'None' sentinel
  - MultiplierResult       â coerces numeric strings, rejects bools,
                              rejects empty strings
  - AIRecommendedStates    â scalar coercion + dedupe
  - MainIndustryExtraction â hyphenated-alias keys work
  - VendorSuppliesExtraction â CSV split into trimmed list
  - EmploymentKeywords     â dedupes, accepts scalar,preserves None
  - RefinedQuery           â rejects prompt-label echo

No LLM, no DB."""

import pytest
from pydantic import ValidationError

from frontend_app.Ai_module.build_from_scratch.schemas import (
    LocationEntry,
    BuildLocationsExtraction,
    CapacityExtraction,
    MultiplierResult,
    AIRecommendedStates,
    MainIndustryExtraction,
)
from frontend_app.Ai_module.vendor_query.schemas import (
    VendorSuppliesExtraction,
)
from frontend_app.Ai_module.employement_query.schemas import (
    EmploymentKeywords,
)
from frontend_app.Ai_module.query_refinement.schemas import (
    RefinedQuery,
)


# ===========================================================================
# LocationEntry â rejects the literal 'None' sentinel
# ===========================================================================

class TestLocationEntry:

    def test_rejects_none_sentinel(self):
        # The LLM sometimes emits 'None' when nolocation is
        # mentioned. Validator must reject â otherwisedownstream code
        # treats 'None' as a real place.
        with pytest.raises(ValidationError):
            LocationEntry(Location="None")

    def test_rejects_none_sentinel_lowercase(self):
        with pytest.raises(ValidationError):
            LocationEntry(Location="none")


# ===========================================================================
# BuildLocationsExtraction â coerces plain strings into {"Location": ...}
# ===========================================================================

class TestBuildLocationsExtraction:

    def test_coerces_string_items_to_dicts(self):
        # The prompt sometimes returns plain strings instead of the
        # documented [{"Location": "Pune"}, ...]. Validator must accept both.
        result = BuildLocationsExtraction(Locations=["Pune", "Mumbai"])
        assert len(result.Locations) == 2
        assert result.Locations[0].Location == "Pune"
        assert result.Locations[1].Location == "Mumbai"

    def test_accepts_mixed_string_and_dict(self):
        result = BuildLocationsExtraction(
            Locations=["Pune", {"Location": "Mumbai"}],
        )
        assert len(result.Locations) == 2


# ===========================================================================
# CapacityExtraction â numeric coercion, boolrejection, None sentinel
# ===========================================================================

class TestCapacityExtraction:

    def test_coerces_numeric_string(self):
        # LLM commonly returns numbers as "1,500" â must coerce to 1500.0.
        result = CapacityExtraction(**{
            "Capacity": "1,500",
            "Capacity Unit": "tons",
            "Time Period": "per annum",
        })
        assert result.capacity == 1500.0

    def test_rejects_bool(self):
        # bool is a subclass of int in Python âexplicit reject prevents
        # True/False silently coercing to 1.0/0.0.
        with pytest.raises(ValidationError):
            CapacityExtraction(**{
                "Capacity": True,
                "Capacity Unit": "tons",
                "Time Period": "per annum",
            })

    def test_accepts_none_sentinel(self):
        # Prompt allows "None" when no capacity given.
        result = CapacityExtraction(**{
            "Capacity": "None",
            "Capacity Unit": "tons",
            "Time Period": "per annum",
        })
        assert result.capacity == "None"


# ===========================================================================
# MultiplierResult â numeric coercion, bool rejection, empty-string rejection
# ===========================================================================

class TestMultiplierResult:

    def test_coerces_numeric_string(self):
        result = MultiplierResult(Multiplier="3.14")
        assert result.Multiplier == 3.14

    def test_rejects_bool(self):
        with pytest.raises(ValidationError):
            MultiplierResult(Multiplier=True)

    def test_rejects_empty_string(self):
        # An empty Multiplier would no-op a real
        # unit conversion â must surface as a failure.
        with pytest.raises(ValidationError):
            MultiplierResult(Multiplier="")


# ===========================================================================
# AIRecommendedStates â scalar coercion + dedupe
# ===========================================================================

class TestAIRecommendedStates:

    def test_coerces_scalar_to_list(self):
        # LLM sometimes returns a single string instead of a 1-element list.
        result = AIRecommendedStates(states="Maharashtra")
        assert result.states == ["Maharashtra"]

    def test_dedupes_preserving_order(self):
        result = AIRecommendedStates(
            states=["Maharashtra", "Gujarat", "Maharashtra", "Karnataka"],
        )
        assert result.states == ["Maharashtra", "Gujarat", "Karnataka"]


# ===========================================================================
# MainIndustryExtraction â hyphenated alias keys
# ===========================================================================

class TestMainIndustryExtraction:

    def test_alias_keys_work(self):
        # LLM emits hyphenated keys ("Main-Industry","Forced-Mapping"
        # etc.) â schema must accept them viaField(alias=...).
        result = MainIndustryExtraction(**{
            "Main-Industry": "Textiles",
            "Original-Inferred-Main-Industry": "Cotton Textiles",
            "Forced-Mapping": "No",
            "Product": "Yarn",
        })
        assert result.main_industry == "Textiles"
        assert result.forced_mapping == "No"
        assert result.product == "Yarn"


# ===========================================================================
# VendorSuppliesExtraction â CSV split
# ===========================================================================

class TestVendorSuppliesExtraction:

    def test_csv_string_splits_into_trimmed_list(self):
        result = VendorSuppliesExtraction(Supplies="steel, cement , glass")
        assert result.Supplies == ["steel", "cement","glass"]

    def test_empty_string_yields_empty_list(self):
        # "no supplies" case â empty list output here.
        result = VendorSuppliesExtraction(Supplies="")
        assert result.Supplies == []


# ===========================================================================
# EmploymentKeywords â dedupe, scalar tolerance, Nonepreservation
# ===========================================================================

class TestEmploymentKeywords:

    def test_dedupes_preserving_order(self):
        result = EmploymentKeywords(KEYWORDS=["Skilled", "Skilled","Unskilled"])
        assert result.KEYWORDS == ["Skilled", "Unskilled"]

    def test_accepts_scalar_string(self):
        # LLM occasionally returns "Skilled" instead of ["Skilled"].
        result = EmploymentKeywords(KEYWORDS="Skilled")
        assert result.KEYWORDS == ["Skilled"]

    def test_none_preserved(self):
        # None is a meaningful sentinel for "general employment, no skill
        # filter" â must NOT become [].
        result = EmploymentKeywords(KEYWORDS=None)
        assert result.KEYWORDS is None


# ===========================================================================
# RefinedQuery â rejects prompt-label echo
# ===========================================================================

class TestRefinedQuery:

    def test_rejects_prompt_label_echo(self):
        # If the LLM echoes the "Reformulated standalone
        # query:" prefix instead of the actual query, the legacy regex
        # would pass it through â validator mustreject.
        with pytest.raises(ValidationError):
            RefinedQuery(
                refined_query="Reformulated standalone query: vendors in Pune?",
            )