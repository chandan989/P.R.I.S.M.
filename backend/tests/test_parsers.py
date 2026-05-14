"""
P.R.I.S.M. Parser Tests

Tests for deliberation parsing, claim extraction, and logprobs parsing.
"""

import pytest
from parsers import DeliberationParser, ClaimExtractor, LogprobsParser
from parsers.deliberation import DeliberationTrace, Hypothesis
from parsers.claim_extractor import Claim, ClaimType
from parsers.logprobs import SequenceLogprobs, ConfidenceMetrics


class TestDeliberationParser:
    """Tests for DeliberationParser."""

    def test_parse_deliberation(self, sample_deliberation_text):
        """Test parsing deliberation from text."""
        parser = DeliberationParser()
        trace = parser.parse(sample_deliberation_text)

        assert trace is not None
        assert isinstance(trace, DeliberationTrace)
        assert len(trace.competing_hypotheses) > 0
        assert len(trace.logical_chain) > 0
        assert trace.selected_interpretation is not None

    def test_parse_hypotheses(self, sample_deliberation_text):
        """Test parsing competing hypotheses."""
        parser = DeliberationParser()
        trace = parser.parse(sample_deliberation_text)

        assert len(trace.competing_hypotheses) == 2

        # Check first hypothesis
        h1 = trace.competing_hypotheses[0]
        assert h1.interpretation == "Clarithromycin significantly increases warfarin levels"
        assert h1.probability == 0.85
        assert len(h1.supporting_evidence) > 0
        assert len(h1.weakening_evidence) > 0

    def test_parse_logical_chain(self, sample_deliberation_text):
        """Test parsing logical chain."""
        parser = DeliberationParser()
        trace = parser.parse(sample_deliberation_text)

        assert len(trace.logical_chain) == 4

        # Check first step
        step1 = trace.logical_chain[0]
        assert step1.step_number == 1
        assert "CYP3A4" in step1.description

    def test_parse_discarded_paths(self, sample_deliberation_text):
        """Test parsing discarded paths."""
        parser = DeliberationParser()
        trace = parser.parse(sample_deliberation_text)

        assert len(trace.discarded_paths) == 1
        assert "No interaction" in trace.discarded_paths[0].hypothesis

    def test_parse_empty_text(self):
        """Test parsing text without deliberation."""
        parser = DeliberationParser()
        trace = parser.parse("This is just regular text without thought blocks.")

        assert trace is None

    def test_to_dict(self, sample_deliberation_text):
        """Test converting trace to dictionary."""
        parser = DeliberationParser()
        trace = parser.parse(sample_deliberation_text)
        trace_dict = parser.to_dict(trace)

        assert "competing_hypotheses" in trace_dict
        assert "discarded_paths" in trace_dict
        assert "logical_chain" in trace_dict
        assert "selected_interpretation" in trace_dict


class TestClaimExtractor:
    """Tests for ClaimExtractor."""

    def test_extract_claims(self, sample_claims_text):
        """Test extracting claims from text."""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_claims_text)

        assert len(claims) > 0
        assert all(isinstance(c, Claim) for c in claims)

    def test_claim_types(self, sample_claims_text):
        """Test claim type classification."""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_claims_text)

        # Should have various claim types
        claim_types = {c.claim_type for c in claims}
        assert ClaimType.DRUG_INTERACTION in claim_types or len(claims) > 0

    def test_drug_extraction(self, sample_claims_text):
        """Test drug name extraction."""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_claims_text)

        # At least one claim should mention drugs
        drug_claims = [c for c in claims if c.drugs_mentioned]
        assert len(drug_claims) > 0

    def test_confidence_calculation(self, sample_claims_text):
        """Test confidence score calculation."""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_claims_text)

        # All claims should have confidence scores
        assert all(0 <= c.confidence <= 1 for c in claims)

    def test_filter_claims(self, sample_claims_text):
        """Test filtering claims by confidence."""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_claims_text)

        # Filter by confidence
        filtered = extractor.filter_claims(claims, min_confidence=0.5)
        assert all(c.confidence >= 0.5 for c in filtered)

    def test_to_dict(self, sample_claims_text):
        """Test converting claim to dictionary."""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_claims_text)

        if claims:
            claim_dict = extractor.to_dict(claims[0])
            assert "text" in claim_dict
            assert "claim_type" in claim_dict
            assert "drugs_mentioned" in claim_dict
            assert "confidence" in claim_dict


class TestLogprobsParser:
    """Tests for LogprobsParser."""

    def test_parse_logprobs(self, sample_logprobs_data):
        """Test parsing logprobs from data."""
        parser = LogprobsParser(temperature=0.7)
        sequence = parser.parse_logprobs(sample_logprobs_data)

        assert sequence is not None
        assert isinstance(sequence, SequenceLogprobs)
        assert len(sequence.tokens) == len(sample_logprobs_data)

    def test_calculate_confidence(self, sample_logprobs_data):
        """Test confidence calculation from logprobs."""
        parser = LogprobsParser(temperature=0.7)
        sequence = parser.parse_logprobs(sample_logprobs_data)
        confidence = parser.calculate_confidence(sequence)

        assert isinstance(confidence, ConfidenceMetrics)
        assert 0 <= confidence.token_level_confidence <= 1
        assert 0 <= confidence.sequence_level_confidence <= 1

    def test_perplexity_calculation(self, sample_logprobs_data):
        """Test perplexity calculation."""
        parser = LogprobsParser(temperature=0.7)
        sequence = parser.parse_logprobs(sample_logprobs_data)

        assert sequence.perplexity > 0
        assert sequence.average_logprob < 0

    def test_detect_uncertainty(self, sample_logprobs_data):
        """Test uncertainty detection."""
        parser = LogprobsParser(temperature=0.7)
        sequence = parser.parse_logprobs(sample_logprobs_data)

        is_uncertain, reasons = parser.detect_uncertainty(sequence, threshold=0.3)

        # Should return a tuple
        assert isinstance(is_uncertain, bool)
        assert isinstance(reasons, list)

    def test_calibrate_confidence(self, sample_logprobs_data):
        """Test confidence calibration."""
        parser = LogprobsParser(temperature=0.7)
        sequence = parser.parse_logprobs(sample_logprobs_data)

        # Without calibration data, should return raw confidence
        calibrated = parser.calibrate_confidence(0.8)
        assert calibrated == 0.8

        # With calibration data
        calibration_data = {"temperature": 1.5}
        calibrated = parser.calibrate_confidence(0.8, calibration_data)
        assert 0 <= calibrated <= 1

    def test_to_dict(self, sample_logprobs_data):
        """Test converting sequence to dictionary."""
        parser = LogprobsParser(temperature=0.7)
        sequence = parser.parse_logprobs(sample_logprobs_data)
        sequence_dict = parser.to_dict(sequence)

        assert "tokens" in sequence_dict
        assert "total_logprob" in sequence_dict
        assert "average_logprob" in sequence_dict
        assert "perplexity" in sequence_dict
