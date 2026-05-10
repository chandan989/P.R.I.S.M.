"""
P.R.I.S.M. Claim Extractor

Extracts factual claims from model responses for selective verification.

Focuses on pharmacological assertions that need verification:
- Drug-drug interactions
- Contraindications
- Dosage recommendations
- Side effects
- Metabolic pathway claims
"""

import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Types of claims that can be extracted."""
    DRUG_INTERACTION = "drug_interaction"
    CONTRAINDICATION = "contraindication"
    DOSAGE = "dosage"
    SIDE_EFFECT = "side_effect"
    METABOLIC_PATHWAY = "metabolic_pathway"
    EFFICACY = "efficacy"
    SAFETY = "safety"
    GENERAL = "general"


@dataclass
class Claim:
    """A factual claim extracted from text."""
    text: str
    claim_type: ClaimType
    drugs_mentioned: List[str]
    confidence: float
    context: str
    position: tuple  # (start, end) in original text


class ClaimExtractor:
    """
    Extracts factual claims from text for verification.

    Uses pattern matching and heuristics to identify
    pharmacological claims that need verification.
    """

    # Drug name patterns (simplified - would use NER in production)
    DRUG_PATTERNS = [
        r'\b[A-Z][a-z]*(?:ox|in|ol|ine|azole|pril|statin|ide|one|ium)\b',
        r'\b(?:warfarin|clarithromycin|metformin|lisinopril|atorvastatin|amlodipine|metoprolol|levothyroxine|omeprazole|sertraline|gabapentin|prednisone|furosemide|allopurinol)\b',
    ]

    # Claim type patterns
    CLAIM_PATTERNS = {
        ClaimType.DRUG_INTERACTION: [
            r'interact[s]?\s+(?:with|between)',
            r'contraindicated\s+(?:with|for)',
            r'increases?\s+(?:the\s+)?(?:level|concentration|effect)',
            r'decreases?\s+(?:the\s+)?(?:level|concentration|effect)',
            r'potentiates?\s+(?:the\s+)?(?:effect|toxicity)',
            r'inhibits?\s+(?:CYP\d+[A-Z]?\d*)',
        ],
        ClaimType.CONTRAINDICATION: [
            r'contraindicated',
            r'should\s+not\s+be\s+used',
            r'avoid\s+(?:using|administration)',
            r'not\s+recommended',
        ],
        ClaimType.DOSAGE: [
            r'\d+\s*(?:mg|mcg|g|ml|units?)\s*(?:daily|twice|once|per\s+day)',
            r'dose\s+(?:of|is|should\s+be)',
            r'dosage\s+(?:of|is|should\s+be)',
        ],
        ClaimType.SIDE_EFFECT: [
            r'(?:cause|causes|caused)\s+(?:the\s+)?(?:following\s+)?(?:side\s+effects?|adverse\s+effects?)',
            r'(?:may|can|might)\s+cause',
            r'common\s+side\s+effects?\s+(?:include|are)',
        ],
        ClaimType.METABOLIC_PATHWAY: [
            r'metabolized\s+by',
            r'(?:substrate|inhibitor|inducer)\s+of\s+(?:CYP\d+[A-Z]?\d*)',
            r'cleared\s+(?:via|through)',
        ],
        ClaimType.EFFICACY: [
            r'effective\s+(?:for|in|against)',
            r'treats?\s+(?:the\s+)?',
            r'indicated\s+(?:for|to)',
        ],
        ClaimType.SAFETY: [
            r'safe\s+(?:to\s+use|for)',
            r'safety\s+(?:profile|concern)',
            r'risk\s+(?:of|associated\s+with)',
        ],
    }

    # Sentence patterns for extraction
    SENTENCE_PATTERN = re.compile(
        r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
    )

    def __init__(self):
        """Initialize the claim extractor."""
        # Compile regex patterns
        self.compiled_drug_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.DRUG_PATTERNS
        ]

        self.compiled_claim_patterns = {
            claim_type: [
                re.compile(pattern, re.IGNORECASE)
                for pattern in patterns
            ]
            for claim_type, patterns in self.CLAIM_PATTERNS.items()
        }

    def extract_claims(self, text: str) -> List[Claim]:
        """
        Extract factual claims from text.

        Args:
            text: Text to extract claims from

        Returns:
            List of extracted claims
        """
        claims = []

        # Split into sentences
        sentences = self._split_sentences(text)

        for sentence in sentences:
            # Determine claim type
            claim_type = self._classify_claim(sentence)

            if claim_type != ClaimType.GENERAL:
                # Extract drug names
                drugs = self._extract_drugs(sentence)

                # Calculate confidence based on pattern strength
                confidence = self._calculate_confidence(sentence, claim_type)

                # Create claim
                claim = Claim(
                    text=sentence.strip(),
                    claim_type=claim_type,
                    drugs_mentioned=drugs,
                    confidence=confidence,
                    context=self._get_context(text, sentence),
                    position=self._find_position(text, sentence)
                )

                claims.append(claim)

        logger.info(f"Extracted {len(claims)} claims from {len(sentences)} sentences")
        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _classify_claim(self, sentence: str) -> ClaimType:
        """
        Classify the type of claim in a sentence.

        Args:
            sentence: Sentence to classify

        Returns:
            Claim type
        """
        # Check each claim type pattern
        for claim_type, patterns in self.compiled_claim_patterns.items():
            for pattern in patterns:
                if pattern.search(sentence):
                    return claim_type

        return ClaimType.GENERAL

    def _extract_drugs(self, text: str) -> List[str]:
        """
        Extract drug names from text.

        Args:
            text: Text to extract drugs from

        Returns:
            List of drug names
        """
        drugs = set()

        for pattern in self.compiled_drug_patterns:
            matches = pattern.findall(text)
            drugs.update(matches)

        return sorted(list(drugs))

    def _calculate_confidence(self, sentence: str, claim_type: ClaimType) -> float:
        """
        Calculate confidence score for a claim.

        Args:
            sentence: Claim sentence
            claim_type: Type of claim

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.5

        # Increase confidence for specific claim types
        if claim_type in [ClaimType.DRUG_INTERACTION, ClaimType.CONTRAINDICATION]:
            confidence += 0.2

        # Increase confidence for sentences with drug names
        drugs = self._extract_drugs(sentence)
        if len(drugs) >= 2:
            confidence += 0.2

        # Increase confidence for specific patterns
        if any(word in sentence.lower() for word in ['significantly', 'strongly', 'potently']):
            confidence += 0.1

        # Cap at 1.0
        return min(confidence, 1.0)

    def _get_context(self, full_text: str, sentence: str) -> str:
        """
        Get surrounding context for a sentence.

        Args:
            full_text: Full text
            sentence: Target sentence

        Returns:
            Context string
        """
        # Find sentence position
        idx = full_text.find(sentence)
        if idx == -1:
            return ""

        # Get 100 characters before and after
        start = max(0, idx - 100)
        end = min(len(full_text), idx + len(sentence) + 100)

        return full_text[start:end]

    def _find_position(self, full_text: str, sentence: str) -> tuple:
        """
        Find the position of a sentence in the full text.

        Args:
            full_text: Full text
            sentence: Target sentence

        Returns:
            Tuple of (start, end) positions
        """
        start = full_text.find(sentence)
        if start == -1:
            return (0, 0)

        return (start, start + len(sentence))

    def filter_claims(
        self,
        claims: List[Claim],
        min_confidence: float = 0.5,
        claim_types: Optional[List[ClaimType]] = None
    ) -> List[Claim]:
        """
        Filter claims by confidence and type.

        Args:
            claims: List of claims to filter
            min_confidence: Minimum confidence threshold
            claim_types: List of claim types to include (None = all)

        Returns:
            Filtered list of claims
        """
        filtered = []

        for claim in claims:
            # Check confidence
            if claim.confidence < min_confidence:
                continue

            # Check claim type
            if claim_types and claim.claim_type not in claim_types:
                continue

            filtered.append(claim)

        return filtered

    def to_dict(self, claim: Claim) -> Dict:
        """
        Convert claim to dictionary.

        Args:
            claim: Claim to convert

        Returns:
            Dictionary representation
        """
        return {
            "text": claim.text,
            "claim_type": claim.claim_type.value,
            "drugs_mentioned": claim.drugs_mentioned,
            "confidence": claim.confidence,
            "context": claim.context,
            "position": claim.position
        }


def main():
    """Test the claim extractor."""
    example_text = """
    The patient is taking warfarin and clarithromycin together.
    Clarithromycin significantly increases warfarin levels through CYP3A4 inhibition.
    This interaction is contraindicated and may cause severe bleeding.
    The recommended warfarin dose is 5mg daily.
    Common side effects of warfarin include bleeding and bruising.
    """

    extractor = ClaimExtractor()
    claims = extractor.extract_claims(example_text)

    print(f"Extracted {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"\n{i}. {claim.claim_type.value} (confidence: {claim.confidence:.2f})")
        print(f"   Text: {claim.text}")
        print(f"   Drugs: {', '.join(claim.drugs_mentioned)}")


if __name__ == "__main__":
    main()
