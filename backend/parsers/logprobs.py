"""
P.R.I.S.M. Logprobs Parser

Extracts and processes logprobs from Gemma 4 responses for
confidence calibration and uncertainty estimation.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Information about a single token."""
    token: str
    token_id: int
    logprob: float
    probability: float


@dataclass
class SequenceLogprobs:
    """Logprobs for a generated sequence."""
    tokens: List[TokenInfo]
    total_logprob: float
    average_logprob: float
    perplexity: float


@dataclass
class ConfidenceMetrics:
    """Confidence metrics derived from logprobs."""
    token_level_confidence: float
    sequence_level_confidence: float
    entropy: float
    variance: float
    calibration_score: Optional[float] = None


class LogprobsParser:
    """
    Parser for Gemma 4 logprobs.

    Extracts confidence metrics from token-level
    logprob information.
    """

    def __init__(self, temperature: float = 0.7):
        """
        Initialize the logprobs parser.

        Args:
            temperature: Sampling temperature used
        """
        self.temperature = temperature

    def parse_logprobs(
        self,
        logprobs_data: List[Dict[str, Any]]
    ) -> Optional[SequenceLogprobs]:
        """
        Parse logprobs from raw data.

        Args:
            logprobs_data: Raw logprobs data from model

        Returns:
            Sequence logprobs if successful
        """
        if not logprobs_data:
            logger.warning("No logprobs data provided")
            return None

        tokens = []

        for token_data in logprobs_data:
            token = token_data.get("token", "")
            token_id = token_data.get("token_id", -1)
            logprob = token_data.get("logprob", 0.0)

            # Convert logprob to probability
            probability = np.exp(logprob)

            tokens.append(TokenInfo(
                token=token,
                token_id=token_id,
                logprob=logprob,
                probability=probability
            ))

        # Calculate metrics
        total_logprob = sum(t.logprob for t in tokens)
        average_logprob = total_logprob / len(tokens) if tokens else 0.0

        # Calculate perplexity
        perplexity = np.exp(-average_logprob) if average_logprob != 0 else float('inf')

        return SequenceLogprobs(
            tokens=tokens,
            total_logprob=total_logprob,
            average_logprob=average_logprob,
            perplexity=perplexity
        )

    def calculate_confidence(
        self,
        sequence_logprobs: SequenceLogprobs
    ) -> ConfidenceMetrics:
        """
        Calculate confidence metrics from logprobs.

        Args:
            sequence_logprobs: Sequence logprobs

        Returns:
            Confidence metrics
        """
        if not sequence_logprobs.tokens:
            return ConfidenceMetrics(
                token_level_confidence=0.0,
                sequence_level_confidence=0.0,
                entropy=0.0,
                variance=0.0
            )

        # Token-level confidence (average probability)
        token_level_confidence = np.mean([
            t.probability for t in sequence_logprobs.tokens
        ])

        # Sequence-level confidence (based on perplexity)
        # Lower perplexity = higher confidence
        sequence_level_confidence = 1.0 / (1.0 + sequence_logprobs.perplexity)

        # Calculate entropy
        probabilities = [t.probability for t in sequence_logprobs.tokens]
        entropy = -sum(p * np.log(p + 1e-10) for p in probabilities)

        # Calculate variance
        variance = np.var(probabilities)

        return ConfidenceMetrics(
            token_level_confidence=float(token_level_confidence),
            sequence_level_confidence=float(sequence_level_confidence),
            entropy=float(entropy),
            variance=float(variance)
        )

    def calibrate_confidence(
        self,
        raw_confidence: float,
        calibration_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Apply temperature scaling or other calibration to raw confidence.

        Args:
            raw_confidence: Raw confidence score
            calibration_data: Optional calibration parameters

        Returns:
            Calibrated confidence score
        """
        if calibration_data:
            # Apply temperature scaling
            temperature = calibration_data.get("temperature", 1.0)
            if temperature != 1.0:
                # Apply temperature scaling
                logit = np.log(raw_confidence / (1 - raw_confidence + 1e-10))
                scaled_logit = logit / temperature
                calibrated = 1.0 / (1.0 + np.exp(-scaled_logit))
                return float(calibrated)

        return raw_confidence

    def detect_uncertainty(
        self,
        sequence_logprobs: SequenceLogprobs,
        threshold: float = 0.3
    ) -> Tuple[bool, List[str]]:
        """
        Detect if the model is uncertain about its response.

        Args:
            sequence_logprobs: Sequence logprobs
            threshold: Uncertainty threshold

        Returns:
            Tuple of (is_uncertain, reasons)
        """
        reasons = []

        # Check perplexity
        if sequence_logprobs.perplexity > 100:
            reasons.append(f"High perplexity: {sequence_logprobs.perplexity:.2f}")

        # Check average logprob
        if sequence_logprobs.average_logprob < -2.0:
            reasons.append(f"Low average logprob: {sequence_logprobs.average_logprob:.2f}")

        # Check for low-probability tokens
        low_prob_tokens = [
            t.token for t in sequence_logprobs.tokens
            if t.probability < 0.1
        ]
        if len(low_prob_tokens) > len(sequence_logprobs.tokens) * 0.5:
            reasons.append(f"Many low-probability tokens: {len(low_prob_tokens)}/{len(sequence_logprobs.tokens)}")

        # Check entropy
        confidence = self.calculate_confidence(sequence_logprobs)
        if confidence.entropy > 2.0:
            reasons.append(f"High entropy: {confidence.entropy:.2f}")

        is_uncertain = len(reasons) > 0

        return is_uncertain, reasons

    def get_top_k_tokens(
        self,
        logprobs_data: List[Dict[str, Any]],
        k: int = 5
    ) -> List[List[Tuple[str, float]]]:
        """
        Get top-k tokens at each position.

        Args:
            logprobs_data: Raw logprobs data
            k: Number of top tokens to return

        Returns:
            List of top-k token lists for each position
        """
        top_k_tokens = []

        for position_data in logprobs_data:
            # Get top logprobs for this position
            top_logprobs = position_data.get("top_logprobs", [])

            # Sort by logprob and take top k
            sorted_tokens = sorted(
                top_logprobs,
                key=lambda x: x.get("logprob", -float('inf')),
                reverse=True
            )[:k]

            # Convert to (token, probability) tuples
            top_k = [
                (t.get("token", ""), np.exp(t.get("logprob", -float('inf'))))
                for t in sorted_tokens
            ]

            top_k_tokens.append(top_k)

        return top_k_tokens

    def to_dict(self, sequence_logprobs: SequenceLogprobs) -> Dict[str, Any]:
        """
        Convert sequence logprobs to dictionary.

        Args:
            sequence_logprobs: Sequence logprobs

        Returns:
            Dictionary representation
        """
        return {
            "tokens": [
                {
                    "token": t.token,
                    "token_id": t.token_id,
                    "logprob": t.logprob,
                    "probability": t.probability
                }
                for t in sequence_logprobs.tokens
            ],
            "total_logprob": sequence_logprobs.total_logprob,
            "average_logprob": sequence_logprobs.average_logprob,
            "perplexity": sequence_logprobs.perplexity
        }


def main():
    """Test the logprobs parser."""
    # Example logprobs data
    example_logprobs = [
        {"token": "The", "token_id": 123, "logprob": -0.1},
        {"token": "patient", "token_id": 456, "logprob": -0.2},
        {"token": "is", "token_id": 789, "logprob": -0.15},
        {"token": "at", "token_id": 101, "logprob": -0.3},
        {"token": "risk", "token_id": 234, "logprob": -0.25},
    ]

    parser = LogprobsParser(temperature=0.7)

    # Parse logprobs
    sequence_logprobs = parser.parse_logprobs(example_logprobs)

    if sequence_logprobs:
        print("Sequence Logprobs:")
        print(f"  Total logprob: {sequence_logprobs.total_logprob:.4f}")
        print(f"  Average logprob: {sequence_logprobs.average_logprob:.4f}")
        print(f"  Perplexity: {sequence_logprobs.perplexity:.4f}")

        # Calculate confidence
        confidence = parser.calculate_confidence(sequence_logprobs)
        print("\nConfidence Metrics:")
        print(f"  Token-level: {confidence.token_level_confidence:.4f}")
        print(f"  Sequence-level: {confidence.sequence_level_confidence:.4f}")
        print(f"  Entropy: {confidence.entropy:.4f}")
        print(f"  Variance: {confidence.variance:.4f}")

        # Detect uncertainty
        is_uncertain, reasons = parser.detect_uncertainty(sequence_logprobs)
        print(f"\nUncertain: {is_uncertain}")
        if reasons:
            for reason in reasons:
                print(f"  - {reason}")


if __name__ == "__main__":
    main()
