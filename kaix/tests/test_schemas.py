"""Schema tests â one trio per schemas.py file (8 files Ã 3 tests = 24).

For each schema, we test:
  1. A valid payload constructs cleanly.
  2. An invalid payload raises ValidationError.
  3. The failure-envelope sibling can be constructed with the standard
     error + raw_output contract used by parse_llm_response.

No LLM, no DB. Pure pydantic boundary checks."""

import pytest
from pydantic import ValidationError

# 1. query_hints
from kaix.Ai_module.query_hints.schemas import (
    QueryHintList, QueryHintListFailure,
)

# 2. intent_detection
from kaix.Ai_module.intent_detection.schemas import (
    IntentClassification, IntentClassificationFailure,
)

# 3. query_refinement
from kaix.Ai_module.query_refinement.schemas import (
    RefinedQuery, RefinedQueryFailure,
)

# 4. approval_query
from kaix.Ai_module.approval_query.schemas import (
    ApprovalClassification, ApprovalClassificationFailure,
)

# 5. incentive_query
from kaix.Ai_module.incentive_query.schemas import (
    IncentiveClassification, IncentiveClassificationFailure,
)

# 6. vendor_query
from kaix.Ai_module.vendor_query.schemas import (
    VendorClassification, VendorClassificationFailure,
)

# 7. employement_query
from kaix.Ai_module.employement_query.schemas import (
    EmploymentClassification, EmploymentClassificationFailure,
)

# 8. build_from_scratch
from kaix.Ai_module.build_from_scratch.schemas import (
    BuildSetupClassification, BuildSetupClassificationFailure,
)


# ===========================================================================
# 1. query_hints â QueryHintList
# ===========================================================================

class TestQueryHintList:

    def test_valid_payload(self):
        result = QueryHintList(hints=[
            {"query": "Where can I set up textile?", "module": "Build from Scratch"},
            {"query": "Vendors for cotton in Battambang?", "module": "Vendor Search"},
        ])
        assert len(result.hints) == 2
        assert result.hints[0].module == "Build from Scratch"

    def test_rejects_bad_enum(self):
        # 'NotARealModule' is not in the 5 allowed module names.
        with pytest.raises(ValidationError):
            QueryHintList(hints=[
                {"query": "x", "module": "NotARealModule"},
            ])

    def test_failure_envelope_constructs(self):
        env = QueryHintListFailure(
            error="markdown fence",
            raw_output="```json\n[]\n```",
        )
        assert env.error == "markdown fence"
        assert env.raw_output.startswith("```")


# ===========================================================================
# 2. intent_detection â IntentClassification
# ===========================================================================

class TestIntentClassification:

    def test_valid_payload(self):
        result = IntentClassification(categories=[
            "Query to search Vendors",
            "Query to Get Approvals",
        ])
        assert len(result.categories) == 2

    def test_rejects_bad_enum(self):
        with pytest.raises(ValidationError):
            IntentClassification(categories=["bogus category"])

    def test_failure_envelope_constructs(self):
        env = IntentClassificationFailure(
            error="empty list after dedup",
            raw_output="[]",
        )
        assert env.error == "empty list after dedup"


# ===========================================================================
# 3. query_refinement â RefinedQuery
# ===========================================================================

class TestRefinedQuery:

    def test_valid_payload(self):
        result = RefinedQuery(refined_query="What vendors supply steel in Pune?")
        assert "Pune" in result.refined_query

    def test_rejects_multiparagraph(self):
        # Validator rejects multi-paragraph reasoning
        # blobs are not single standalone queries.
        with pytest.raises(ValidationError):
            RefinedQuery(refined_query="Para 1.\n\nPara 2.")

    def test_failure_envelope_constructs(self):
        env = RefinedQueryFailure(
            error="empty string",
            raw_output="",
        )
        assert env.error == "empty string"


# ===========================================================================
# 4. approval_query â ApprovalClassification
# ===========================================================================

class TestApprovalClassification:

    def test_valid_payload(self):
        result = ApprovalClassification(classification_number=3)
        assert result.classification_number == 3

    def test_rejects_out_of_range(self):
        # Approval categories are 1-5 only; 6 must be rejected.
        with pytest.raises(ValidationError):
            ApprovalClassification(classification_number=6)

    def test_failure_envelope_constructs(self):
        env = ApprovalClassificationFailure(
            error="prose returned",
            raw_output="Sure, the answer is 3.",
        )
        assert env.classification_number is None
        assert env.raw_output.startswith("Sure")


# ===========================================================================
# 5. incentive_query â IncentiveClassification
# ===========================================================================

class TestIncentiveClassification:

    def test_valid_payload(self):
        result = IncentiveClassification(classification_number=1)
        assert result.classification_number == 1

    def test_rejects_out_of_range(self):
        # 0 is below the allowed 1-5 range.
        with pytest.raises(ValidationError):
            IncentiveClassification(classification_number=0)

    def test_failure_envelope_constructs(self):
        env = IncentiveClassificationFailure(
            error="word instead of digit",
            raw_output="two",
        )
        assert env.error == "word instead of digit"


# ===========================================================================
# 6. vendor_query â VendorClassification
# ===========================================================================

class TestVendorClassification:

    def test_valid_payload(self):
        result = VendorClassification(classification_number=4)
        assert result.classification_number == 4

    def test_rejects_out_of_range(self):
        # Vendor categories are 1-7 only; 8 must be rejected.
        with pytest.raises(ValidationError):
            VendorClassification(classification_number=8)

    def test_failure_envelope_constructs(self):
        env = VendorClassificationFailure(
            error="multi-token output",
            raw_output="1, 3",
        )
        assert env.raw_output == "1, 3"


# ===========================================================================
# 7. employement_query â EmploymentClassification
# ===========================================================================

class TestEmploymentClassification:

    def test_valid_payload(self):
        result = EmploymentClassification(classification_number=2)
        assert result.classification_number == 2

    def test_rejects_out_of_range(self):
        # Employment categories are 1-4 only; 5 must be rejected.
        with pytest.raises(ValidationError):
            EmploymentClassification(classification_number=5)

    def test_failure_envelope_constructs(self):
        env = EmploymentClassificationFailure(
            error="prose instead of digit",
            raw_output="It is two.",
        )
        assert env.classification_number is None


# ===========================================================================
# 8. build_from_scratch â BuildSetupClassification
# ===========================================================================

class TestBuildSetupClassification:

    def test_valid_payload(self):
        result = BuildSetupClassification(classification_number=6)
        assert result.classification_number == 6

    def test_rejects_out_of_range(self):
        # Build-setup categories are 1-6 only; 0 must be rejected.
        with pytest.raises(ValidationError):
            BuildSetupClassification(classification_number=0)

    def test_failure_envelope_constructs(self):
        env = BuildSetupClassificationFailure(
            error="negative number",
            raw_output="-1",
        )
        assert env.error == "negative number"


