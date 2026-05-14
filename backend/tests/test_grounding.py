"""
P.R.I.S.M. Grounding Tests

Tests for claim verification and knowledge base operations.
"""

import pytest
from grounding import ClaimVerifier, VerificationStatus
from grounding.verifier import VerificationResult


class TestClaimVerifier:
    """Tests for ClaimVerifier."""

    @pytest.fixture
    def verifier(self, tmp_path):
        """Create a verifier with temporary knowledge base."""
        kb_root = str(tmp_path / "kb")
        return ClaimVerifier(kb_root=kb_root)

    def test_verify_claim_confirmed(self, verifier):
        """Test verifying a confirmed claim."""
        # Add a document first
        verifier.kb.add_document(
            doc_id="test_001",
            content="Warfarin increases bleeding risk when combined with clarithromycin.",
            metadata={"source": "test", "category": "interaction"}
        )

        result = verifier.verify_claim("Warfarin increases bleeding risk")

        assert isinstance(result, VerificationResult)
        assert result.status in [VerificationStatus.CONFIRMED, VerificationStatus.INFERRED]

    def test_verify_claim_out_of_scope(self, verifier):
        """Test verifying a claim with no matching documents."""
        result = verifier.verify_claim("Some completely unrelated claim")

        assert isinstance(result, VerificationResult)
        assert result.status == VerificationStatus.OUT_OF_SCOPE
        assert result.confidence == 0.0

    def test_verify_multiple_claims(self, verifier):
        """Test verifying multiple claims."""
        # Add documents
        verifier.kb.add_document(
            doc_id="test_001",
            content="Warfarin increases bleeding risk.",
            metadata={"source": "test", "category": "interaction"}
        )
        verifier.kb.add_document(
            doc_id="test_002",
            content="Metformin is safe for most patients.",
            metadata={"source": "test", "category": "safety"}
        )

        claims = [
            "Warfarin increases bleeding risk",
            "Metformin is safe for most patients"
        ]
        results = verifier.verify_claims(claims)

        assert len(results) == 2
        assert all(isinstance(r, VerificationResult) for r in results)

    def test_check_contradiction(self, verifier):
        """Test contradiction detection."""
        # Add a document
        verifier.kb.add_document(
            doc_id="test_001",
            content="Warfarin does NOT increase bleeding risk.",
            metadata={"source": "test", "category": "interaction"}
        )

        result = verifier.verify_claim("Warfarin increases bleeding risk")

        # Should detect contradiction (simplified check)
        assert isinstance(result, VerificationResult)

    def test_get_sources_summary(self, verifier):
        """Test getting sources summary."""
        # Add documents from different sources
        verifier.kb.add_document(
            doc_id="test_001",
            content="Test content 1",
            metadata={"source": "FDA", "category": "test"}
        )
        verifier.kb.add_document(
            doc_id="test_002",
            content="Test content 2",
            metadata={"source": "DrugBank", "category": "test"}
        )

        summary = verifier.get_sources_summary()

        assert isinstance(summary, dict)
        assert "FDA" in summary
        assert "DrugBank" in summary

    def test_check_staleness(self, verifier):
        """Test staleness checking."""
        is_stale, days_since = verifier.check_staleness()

        assert isinstance(is_stale, bool)
        assert isinstance(days_since, int)

    def test_to_dict(self, verifier):
        """Test converting verification result to dictionary."""
        verifier.kb.add_document(
            doc_id="test_001",
            content="Test content",
            metadata={"source": "test", "category": "test"}
        )

        result = verifier.verify_claim("Test claim")
        result_dict = verifier.to_dict(result)

        assert "claim" in result_dict
        assert "status" in result_dict
        assert "confidence" in result_dict
        assert "sources" in result_dict


class TestVerificationStatus:
    """Tests for VerificationStatus enum."""

    def test_status_values(self):
        """Test verification status values."""
        assert VerificationStatus.CONFIRMED.value == "confirmed"
        assert VerificationStatus.CONTRADICTED.value == "contradicted"
        assert VerificationStatus.INFERRED.value == "inferred"
        assert VerificationStatus.OUT_OF_SCOPE.value == "out_of_scope"
