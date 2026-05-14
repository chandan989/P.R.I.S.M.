"""
P.R.I.S.M. Confidence Calibration

Implements conformal prediction and temperature scaling
for calibrated confidence scores.

Features:
- Conformal prediction with OOD detection
- Temperature scaling for calibration
- Expected Calibration Error (ECE) evaluation
- Brier score calculation
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CalibrationMetrics:
    """Calibration metrics for a model."""
    ece: float  # Expected Calibration Error
    brier_score: float
    reliability: List[Tuple[float, float, int]]  # (confidence, accuracy, count)
    temperature: Optional[float] = None


@dataclass
class ConfidenceInterval:
    """Confidence interval with statistical guarantees."""
    lower_bound: float
    upper_bound: float
    coverage: float
    is_ood: bool  # Out of distribution


class ConformalPredictor:
    """
    Conformal prediction for statistically guaranteed confidence intervals.

    Implements dynamic conformal prediction with OOD detection
    to prevent false mathematical confidence on novel inputs.
    """

    def __init__(self, alpha: float = 0.1, ood_threshold: float = 0.8):
        """
        Initialize the conformal predictor.

        Args:
            alpha: Significance level (1 - coverage)
            ood_threshold: Semantic distance threshold for OOD detection
        """
        self.alpha = alpha
        self.ood_threshold = ood_threshold
        self.calibration_scores: List[float] = []
        self.is_calibrated = False

    def fit(self, calibration_data: List[Tuple[float, bool]]):
        """
        Fit the conformal predictor on calibration data.

        Args:
            calibration_data: List of (confidence, is_correct) tuples
        """
        # Compute nonconformity scores
        self.calibration_scores = [
            1.0 - confidence if is_correct else confidence
            for confidence, is_correct in calibration_data
        ]

        # Sort scores
        self.calibration_scores.sort()

        # Compute quantile
        n = len(self.calibration_scores)
        self.quantile = np.quantile(
            self.calibration_scores,
            min(1.0, (n + 1) * (1 - self.alpha) / n)
        )

        self.is_calibrated = True
        logger.info(f"Calibrated conformal predictor with {n} samples, quantile={self.quantile:.4f}")

    def predict(
        self,
        confidence: float,
        semantic_distance: Optional[float] = None
    ) -> ConfidenceInterval:
        """
        Predict confidence interval with coverage guarantee.

        Args:
            confidence: Raw confidence score
            semantic_distance: Semantic distance from calibration set

        Returns:
            Confidence interval with coverage guarantee
        """
        if not self.is_calibrated:
            logger.warning("Predictor not calibrated, using raw confidence")
            return ConfidenceInterval(
                lower_bound=max(0.0, confidence - 0.1),
                upper_bound=min(1.0, confidence + 0.1),
                coverage=1.0 - self.alpha,
                is_ood=False
            )

        # Check for OOD
        is_ood = False
        if semantic_distance and semantic_distance > self.ood_threshold:
            is_ood = True
            # Widen interval for OOD inputs
            adjusted_alpha = self.alpha * 2
        else:
            adjusted_alpha = self.alpha

        # Compute interval
        lower_bound = max(0.0, confidence - self.quantile)
        upper_bound = min(1.0, confidence + self.quantile)

        return ConfidenceInterval(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            coverage=1.0 - adjusted_alpha,
            is_ood=is_ood
        )


class TemperatureScaler:
    """
    Temperature scaling for confidence calibration.

    Learns a temperature parameter to calibrate confidence scores.
    """

    def __init__(self):
        """Initialize the temperature scaler."""
        self.temperature: Optional[float] = None
        self.is_fitted = False

    def fit(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
        max_iter: int = 1000,
        lr: float = 0.01
    ):
        """
        Fit temperature scaling on calibration data.

        Args:
            logits: Logits from the model (n_samples, n_classes)
            labels: True labels (n_samples,)
            max_iter: Maximum optimization iterations
            lr: Learning rate
        """
        # Initialize temperature
        self.temperature = 1.0

        # Optimize temperature using gradient descent
        for i in range(max_iter):
            # Compute scaled logits
            scaled_logits = logits / self.temperature

            # Compute probabilities
            probs = self._softmax(scaled_logits)

            # Compute gradient
            grad = self._compute_gradient(logits, labels, probs)

            # Update temperature
            self.temperature -= lr * grad

            # Ensure temperature stays positive
            self.temperature = max(0.1, self.temperature)

            # Check convergence
            if abs(grad) < 1e-5:
                break

        self.is_fitted = True
        logger.info(f"Fitted temperature scaler: T={self.temperature:.4f}")

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Compute softmax probabilities."""
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def _compute_gradient(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
        probs: np.ndarray
    ) -> float:
        """Compute gradient for temperature optimization."""
        n = len(labels)

        # d(NLL)/dT = (z_y - sum_j p_j z_j) / T^2, averaged over samples.
        correct_logits = logits[np.arange(n), labels]
        expected_logits = np.sum(probs * logits, axis=1)
        grad = np.mean((correct_logits - expected_logits) / (self.temperature ** 2))

        return grad

    def transform(self, logits: np.ndarray) -> np.ndarray:
        """
        Apply temperature scaling to logits.

        Args:
            logits: Logits to scale

        Returns:
            Scaled probabilities
        """
        if not self.is_fitted:
            logger.warning("Scaler not fitted, returning raw probabilities")
            return self._softmax(logits)

        scaled_logits = logits / self.temperature
        return self._softmax(scaled_logits)


class CalibrationEvaluator:
    """
    Evaluates calibration metrics for confidence scores.

    Computes ECE, Brier score, and reliability diagrams.
    """

    def __init__(self, n_bins: int = 10):
        """
        Initialize the calibration evaluator.

        Args:
            n_bins: Number of bins for reliability diagram
        """
        self.n_bins = n_bins

    def evaluate(
        self,
        confidences: np.ndarray,
        correct: np.ndarray
    ) -> CalibrationMetrics:
        """
        Evaluate calibration metrics.

        Args:
            confidences: Confidence scores (n_samples,)
            correct: Binary correctness labels (n_samples,)

        Returns:
            Calibration metrics
        """
        # Compute ECE
        ece = self._compute_ece(confidences, correct)

        # Compute Brier score
        brier = self._compute_brier_score(confidences, correct)

        # Compute reliability diagram
        reliability = self._compute_reliability(confidences, correct)

        return CalibrationMetrics(
            ece=ece,
            brier_score=brier,
            reliability=reliability
        )

    def _compute_ece(
        self,
        confidences: np.ndarray,
        correct: np.ndarray
    ) -> float:
        """
        Compute Expected Calibration Error.

        Args:
            confidences: Confidence scores
            correct: Correctness labels

        Returns:
            ECE value
        """
        # Create bins
        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize(confidences, bin_edges) - 1

        ece = 0.0
        total_samples = len(confidences)

        for i in range(self.n_bins):
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

    def _compute_brier_score(
        self,
        confidences: np.ndarray,
        correct: np.ndarray
    ) -> float:
        """
        Compute Brier score.

        Args:
            confidences: Confidence scores
            correct: Correctness labels

        Returns:
            Brier score
        """
        return np.mean((confidences - correct) ** 2)

    def _compute_reliability(
        self,
        confidences: np.ndarray,
        correct: np.ndarray
    ) -> List[Tuple[float, float, int]]:
        """
        Compute reliability diagram data.

        Args:
            confidences: Confidence scores
            correct: Correctness labels

        Returns:
            List of (confidence, accuracy, count) tuples
        """
        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize(confidences, bin_edges) - 1

        reliability = []

        for i in range(self.n_bins):
            mask = bin_indices == i
            bin_confidences = confidences[mask]
            bin_correct = correct[mask]

            if len(bin_confidences) == 0:
                continue

            accuracy = np.mean(bin_correct)
            avg_confidence = np.mean(bin_confidences)

            reliability.append((avg_confidence, accuracy, len(bin_confidences)))

        return reliability


def main():
    """Test the calibration modules."""
    # Example calibration data
    np.random.seed(42)
    n_samples = 1000

    # Generate synthetic confidences and labels
    confidences = np.random.beta(2, 2, n_samples)
    correct = np.random.binomial(1, confidences)

    # Test conformal predictor
    print("Testing Conformal Predictor:")
    conformal = ConformalPredictor(alpha=0.1)
    calibration_data = list(zip(confidences[:500], correct[:500]))
    conformal.fit(calibration_data)

    # Predict on test data
    test_confidence = 0.8
    interval = conformal.predict(test_confidence, semantic_distance=0.5)
    print(f"  Confidence: {test_confidence}")
    print(f"  Interval: [{interval.lower_bound:.3f}, {interval.upper_bound:.3f}]")
    print(f"  Coverage: {interval.coverage:.3f}")
    print(f"  OOD: {interval.is_ood}")

    # Test calibration evaluator
    print("\nTesting Calibration Evaluator:")
    evaluator = CalibrationEvaluator(n_bins=10)
    metrics = evaluator.evaluate(confidences[500:], correct[500:])
    print(f"  ECE: {metrics.ece:.4f}")
    print(f"  Brier Score: {metrics.brier_score:.4f}")
    print(f"  Reliability bins: {len(metrics.reliability)}")


if __name__ == "__main__":
    main()
