"""
P.R.I.S.M. Brier Score Evaluation

Computes Brier score for calibration evaluation.
"""

import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


def brier_score(confidences: np.ndarray, correct: np.ndarray) -> float:
    """
    Compute Brier score.

    The Brier score measures the mean squared error between
    predicted probabilities and actual outcomes.

    Args:
        confidences: Confidence scores (n_samples,)
        correct: Binary correctness labels (n_samples,)

    Returns:
        Brier score (lower is better)
    """
    return np.mean((confidences - correct) ** 2)


def brier_score_decomposition(
    confidences: np.ndarray,
    correct: np.ndarray
) -> Tuple[float, float, float]:
    """
    Decompose Brier score into reliability, resolution, and uncertainty.

    Args:
        confidences: Confidence scores (n_samples,)
        correct: Binary correctness labels (n_samples,)

    Returns:
        Tuple of (reliability, resolution, uncertainty)
    """
    # Overall frequency
    n = len(confidences)
    frequency = np.mean(correct)

    # Group by unique confidence values
    unique_confidences = np.unique(confidences)

    reliability = 0.0
    resolution = 0.0
    uncertainty = frequency * (1 - frequency)

    for conf in unique_confidences:
        mask = confidences == conf
        n_k = np.sum(mask)

        if n_k == 0:
            continue

        # Observed frequency for this confidence
        obs_freq = np.mean(correct[mask])

        # Reliability component
        reliability += (n_k / n) * (obs_freq - conf) ** 2

        # Resolution component
        resolution += (n_k / n) * (obs_freq - frequency) ** 2

    return reliability, resolution, uncertainty


def main():
    """Test Brier score computation."""
    # Example data
    np.random.seed(42)
    n_samples = 1000

    # Generate synthetic confidences
    confidences = np.random.beta(2, 2, n_samples)

    # Generate correctness based on true probability
    true_probs = confidences
    correct = np.random.binomial(1, true_probs)

    # Compute Brier score
    bs = brier_score(confidences, correct)
    print(f"Brier Score: {bs:.4f}")

    # Decompose Brier score
    reliability, resolution, uncertainty = brier_score_decomposition(
        confidences, correct
    )
    print(f"\nBrier Score Decomposition:")
    print(f"  Reliability: {reliability:.4f}")
    print(f"  Resolution: {resolution:.4f}")
    print(f"  Uncertainty: {uncertainty:.4f}")
    print(f"  Sum: {reliability - resolution + uncertainty:.4f}")


if __name__ == "__main__":
    main()
