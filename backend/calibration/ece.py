"""
P.R.I.S.M. Expected Calibration Error (ECE) Evaluation

Computes Expected Calibration Error for confidence calibration evaluation.
"""

import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


def expected_calibration_error(
    confidences: np.ndarray,
    correct: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Compute Expected Calibration Error (ECE).

    ECE measures the weighted average difference between
    predicted confidence and observed accuracy across bins.

    Args:
        confidences: Confidence scores (n_samples,)
        correct: Binary correctness labels (n_samples,)
        n_bins: Number of bins for the reliability diagram

    Returns:
        ECE value (lower is better)
    """
    # Create bins
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(confidences, bin_edges) - 1

    ece = 0.0
    total_samples = len(confidences)

    for i in range(n_bins):
        # Get samples in this bin
        mask = bin_indices == i
        bin_confidences = confidences[mask]
        bin_correct = correct[mask]

        if len(bin_confidences) == 0:
            continue

        # Compute accuracy and average confidence
        accuracy = np.mean(bin_correct)
        avg_confidence = np.mean(bin_confidences)

        # Weight by bin size
        weight = len(bin_confidences) / total_samples
        ece += weight * abs(accuracy - avg_confidence)

    return ece


def reliability_diagram(
    confidences: np.ndarray,
    correct: np.ndarray,
    n_bins: int = 10
) -> Tuple[List[float], List[float], List[int]]:
    """
    Compute data for reliability diagram.

    Args:
        confidences: Confidence scores (n_samples,)
        correct: Binary correctness labels (n_samples,)
        n_bins: Number of bins

    Returns:
        Tuple of (avg_confidences, accuracies, counts) for each bin
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(confidences, bin_edges) - 1

    avg_confidences = []
    accuracies = []
    counts = []

    for i in range(n_bins):
        mask = bin_indices == i
        bin_confidences = confidences[mask]
        bin_correct = correct[mask]

        if len(bin_confidences) == 0:
            # Empty bin, use bin center
            avg_confidences.append((bin_edges[i] + bin_edges[i + 1]) / 2)
            accuracies.append(0.0)
            counts.append(0)
        else:
            avg_confidences.append(np.mean(bin_confidences))
            accuracies.append(np.mean(bin_correct))
            counts.append(len(bin_confidences))

    return avg_confidences, accuracies, counts


def adaptive_ece(
    confidences: np.ndarray,
    correct: np.ndarray,
    n_bins: int = 15
) -> float:
    """
    Compute Adaptive ECE with equal-mass bins.

    Unlike standard ECE which uses equal-width bins,
    adaptive ECE uses bins with equal number of samples.

    Args:
        confidences: Confidence scores (n_samples,)
        correct: Binary correctness labels (n_samples,)
        n_bins: Number of bins

    Returns:
        Adaptive ECE value
    """
    # Sort by confidence
    sorted_indices = np.argsort(confidences)
    sorted_confidences = confidences[sorted_indices]
    sorted_correct = correct[sorted_indices]

    # Create equal-mass bins
    bin_size = len(confidences) // n_bins
    ece = 0.0

    for i in range(n_bins):
        start = i * bin_size
        end = (i + 1) * bin_size if i < n_bins - 1 else len(confidences)

        bin_confidences = sorted_confidences[start:end]
        bin_correct = sorted_correct[start:end]

        if len(bin_confidences) == 0:
            continue

        # Compute accuracy and average confidence
        accuracy = np.mean(bin_correct)
        avg_confidence = np.mean(bin_confidences)

        # Weight by bin size
        weight = len(bin_confidences) / len(confidences)
        ece += weight * abs(accuracy - avg_confidence)

    return ece


def classwise_ece(
    confidences: np.ndarray,
    labels: np.ndarray,
    n_classes: int,
    n_bins: int = 10
) -> float:
    """
    Compute class-wise ECE for multi-class problems.

    Args:
        confidences: Confidence scores (n_samples, n_classes)
        labels: True labels (n_samples,)
        n_classes: Number of classes
        n_bins: Number of bins

    Returns:
        Class-wise ECE value
    """
    total_ece = 0.0

    for class_idx in range(n_classes):
        # Get confidences and correctness for this class
        class_confidences = confidences[:, class_idx]
        class_correct = (labels == class_idx).astype(float)

        # Compute ECE for this class
        class_ece = expected_calibration_error(
            class_confidences,
            class_correct,
            n_bins
        )

        total_ece += class_ece

    return total_ece / n_classes


def maximum_calibration_error(
    confidences: np.ndarray,
    correct: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Compute Maximum Calibration Error (MCE).

    MCE is the maximum difference between accuracy and confidence
    across all bins.

    Args:
        confidences: Confidence scores (n_samples,)
        correct: Binary correctness labels (n_samples,)
        n_bins: Number of bins

    Returns:
        MCE value
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(confidences, bin_edges) - 1

    max_error = 0.0

    for i in range(n_bins):
        mask = bin_indices == i
        bin_confidences = confidences[mask]
        bin_correct = correct[mask]

        if len(bin_confidences) == 0:
            continue

        accuracy = np.mean(bin_correct)
        avg_confidence = np.mean(bin_confidences)

        error = abs(accuracy - avg_confidence)
        max_error = max(max_error, error)

    return max_error


def main():
    """Test ECE computation."""
    # Example data
    np.random.seed(42)
    n_samples = 1000

    # Generate synthetic confidences (overconfident)
    confidences = np.random.beta(3, 2, n_samples)
    confidences = np.clip(confidences + 0.1, 0.01, 0.99)

    # Generate correctness based on true probability
    true_probs = confidences * 0.8  # Model is overconfident
    correct = np.random.binomial(1, true_probs)

    # Compute ECE
    ece = expected_calibration_error(confidences, correct)
    print(f"Expected Calibration Error: {ece:.4f}")

    # Compute adaptive ECE
    adaptive_ece_val = adaptive_ece(confidences, correct)
    print(f"Adaptive ECE: {adaptive_ece_val:.4f}")

    # Compute MCE
    mce = maximum_calibration_error(confidences, correct)
    print(f"Maximum Calibration Error: {mce:.4f}")

    # Get reliability diagram data
    avg_conf, acc, counts = reliability_diagram(confidences, correct)
    print(f"\nReliability Diagram ({len(avg_conf)} bins):")
    for i, (conf, accuracy, count) in enumerate(zip(avg_conf, acc, counts)):
        if count > 0:
            print(f"  Bin {i}: conf={conf:.3f}, acc={accuracy:.3f}, n={count}")


if __name__ == "__main__":
    main()
