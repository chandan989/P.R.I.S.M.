"""
P.R.I.S.M. Source Grounding Verifier

Verifies factual claims against the curated clinical knowledge base.

Features:
- Dense embedding search using CPU-optimized models
- Selective verification of pharmacological claims
- Source document retrieval and citation
- Contradiction detection
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add knowledge base to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base'))

from knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Verification status for a claim."""
    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    INFERRED = "inferred"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class VerificationResult:
    """Result of verifying a claim."""
    claim: str
    status: VerificationStatus
    confidence: float
    sources: List[Dict[str, Any]]
    evidence: Optional[str] = None
    warning: Optional[str] = None


@dataclass
class SourceEvidence:
    """Evidence from a source document."""
    doc_id: str
    source: str
    category: str
    content: str
    similarity: float
    url: Optional[str] = None


class ClaimVerifier:
    """
    Verifies claims against the knowledge base.

    Uses dense embedding search to find relevant source
    documents and determine verification status.
    """

    def __init__(self, kb_root: str = "./knowledge_base"):
        """
        Initialize the claim verifier.

        Args:
            kb_root: Root path of the knowledge base
        """
        self.kb = KnowledgeBase(kb_root)
        self.verification_threshold = 0.55
        self.contradiction_threshold = 0.70

    def verify_claim(
        self,
        claim: str,
        top_k: int = 5
    ) -> VerificationResult:
        """
        Verify a single claim against the knowledge base.

        Args:
            claim: Claim text to verify
            top_k: Number of top results to consider

        Returns:
            Verification result
        """
        # Search for similar documents
        results = self.kb.search(claim, top_k=top_k, threshold=0.3)

        if not results:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.OUT_OF_SCOPE,
                confidence=0.0,
                sources=[],
                warning="No relevant sources found in knowledge base"
            )

        # Check for contradictions
        contradiction = self._check_contradiction(claim, results)
        if contradiction:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.CONTRADICTED,
                confidence=0.9,
                sources=[contradiction],
                evidence=contradiction.get('content', ''),
                warning="Claim contradicts verified sources"
            )

        # Check for confirmation
        confirmation = self._check_confirmation(claim, results)
        if confirmation:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.CONFIRMED,
                confidence=confirmation['similarity'],
                sources=[confirmation],
                evidence=confirmation.get('content', '')
            )

        # Otherwise, it's inferred
        best_match = results[0]
        return VerificationResult(
            claim=claim,
            status=VerificationStatus.INFERRED,
            confidence=best_match['similarity'],
            sources=results[:2],
            evidence=best_match.get('content', '')
        )

    def verify_claims(
        self,
        claims: List[str],
        top_k: int = 5
    ) -> List[VerificationResult]:
        """
        Verify multiple claims.

        Args:
            claims: List of claim texts to verify
            top_k: Number of top results to consider

        Returns:
            List of verification results
        """
        results = []

        for claim in claims:
            result = self.verify_claim(claim, top_k=top_k)
            results.append(result)

        return results

    def _check_contradiction(
        self,
        claim: str,
        results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a claim contradicts any source.

        Args:
            claim: Claim text
            results: Search results

        Returns:
            Contradicting source if found, None otherwise
        """
        # Simple contradiction detection
        # In production, use NLI model for better accuracy

        claim_lower = claim.lower()

        for result in results:
            content_lower = result['content'].lower()

            # Check for negation patterns
            if self._has_contradiction(claim_lower, content_lower):
                return result

        return None

    def _has_contradiction(self, claim: str, source: str) -> bool:
        """
        Check if claim contradicts source using simple patterns.

        Args:
            claim: Claim text (lowercase)
            source: Source text (lowercase)

        Returns:
            True if contradiction detected
        """
        # Negation indicators
        negation_words = ['not', 'never', 'no', 'cannot', 'unable', 'unlikely']

        # Check if claim has positive assertion but source has negation
        for word in negation_words:
            if word in source and word not in claim:
                # This is a very basic heuristic
                # In production, use proper NLI
                return True

        return False

    def _check_confirmation(
        self,
        claim: str,
        results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a claim is confirmed by sources.

        Args:
            claim: Claim text
            results: Search results

        Returns:
            Confirming source if found, None otherwise
        """
        for result in results:
            if result['similarity'] >= self.verification_threshold:
                return result

        return None

    def get_source_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a source document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document data if found, None otherwise
        """
        return self.kb._load_document(doc_id)

    def get_sources_summary(self) -> Dict[str, int]:
        """
        Get a summary of available sources.

        Returns:
            Dictionary mapping source names to document counts
        """
        return self.kb.get_sources_summary()

    def check_staleness(self) -> Tuple[bool, int]:
        """
        Check if the knowledge base is stale.

        Returns:
            Tuple of (is_stale, days_since_update)
        """
        return self.kb.check_staleness()

    def to_dict(self, result: VerificationResult) -> Dict[str, Any]:
        """
        Convert verification result to dictionary.

        Args:
            result: Verification result

        Returns:
            Dictionary representation
        """
        return {
            "claim": result.claim,
            "status": result.status.value,
            "confidence": result.confidence,
            "sources": result.sources,
            "evidence": result.evidence,
            "warning": result.warning
        }


def main():
    """Test the claim verifier."""
    # Example claims
    example_claims = [
        "Warfarin increases bleeding risk when combined with clarithromycin",
        "Metformin is safe for all patients with renal impairment",
        "Lisinopril is an ACE inhibitor used for hypertension"
    ]

    verifier = ClaimVerifier()

    print("Knowledge Base Status:")
    summary = verifier.get_sources_summary()
    for source, count in summary.items():
        print(f"  {source}: {count} documents")

    print("\nVerifying Claims:")
    for claim in example_claims:
        result = verifier.verify_claim(claim)
        print(f"\nClaim: {claim}")
        print(f"Status: {result.status.value} (confidence: {result.confidence:.2f})")
        if result.warning:
            print(f"Warning: {result.warning}")
        if result.evidence:
            print(f"Evidence: {result.evidence[:100]}...")


if __name__ == "__main__":
    main()
