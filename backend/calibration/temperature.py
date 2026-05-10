"""
P.R.I.S.M. Temperature Scaling

Post-hoc calibration of confidence scores using temperature scaling.
"""

import logging
from typing import List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class TemperatureScaling:
    """
    Temperature scaling for confidence calibration.

    Learns a temperature parameter to calibrate confidence scores
    on a validation set.
    """

    def __init__(self):
        """Initialize the temperature scaler."""
        self.temperature: Optional[float] = None
        self.is_fitted = False

    def fit(
        self,
        confidences: np.ndarray,
        correct: np.ndarray,
        max_iter: int = 1000,
        lr: float = 0.01,
        tol: float = 1e-5
    ):
        """
        Fit temperature scaling on validation data.

        Args:
            confidences: Confidence scores (n_samples,)
            correct: Binary correctness labels (n_samples,)
            max_iter: Maximum optimization iterations
            lr: Learning rate
            tol: Convergence tolerance
        """
        # Initialize temperature
        self.temperature = 1.0

        # Optimize temperature using gradient descent
        prev_loss = float('inf')

        for i in range(max_iter):
            # Compute scaled confidences
            scaled_confidences = self._scale_confidences(confidences)

            # Compute loss (negative log likelihood)
            loss = self._compute_nll(scaled_confidences, correct)

            # Check convergence
            if abs(prev_loss - loss) < tol:
                break

            prev_loss = loss

            # Compute gradient
            grad = self._compute_gradient(confidences, correct, scaled_confidences)

            # Update temperature
            self.temperature -= lr * grad

            # Ensure temperature stays positive
            self.temperature = max(0.1, self.temperature)

        self.is_fitted = True
        logger.info(f"Fitted temperature scaler: T={self.temperature:.4f}, NLL={loss:.4f}")

    def _scale_confidences(self, confidences: np.ndarray) -> np.ndarray:
        """
        Apply temperature scaling to confidences.

        Args:
            confidences: Raw confidences

        Returns:
            Scaled confidences
        """
        # Convert to logits
        logits = np.log(confidences / (1 - confidences + 1e-10))

        # Scale by temperature
        scaled_logits = logits / self.temperature

        # Convert back to probabilities
        scaled_confidences = 1.0 / (1.0 + np.exp(-scaled_logits))

        return scaled_confidences

    def _compute_nll(
        self,
        confidences: np.ndarray,
        correct: np.ndarray
    ) -> float:
        """
        Compute negative log likelihood.

        Args:
            confidences: Confidence scores
            correct: Correctness labels

        Returns:
            Negative log likelihood
        """
        # Avoid log(0)
        eps = 1e-10

        # Compute NLL
        nll = -np.mean(
            correct * np.log(confidences + eps) +
            (1 - correct) * np.log(1 - confidences + eps)
        )

        return nll

    def _compute_gradient(
        self,
        confidences: np.ndarray,
        correct: np.ndarray,
        scaled_confidences: np.ndarray
    ) -> float:
        """
        Compute gradient for temperature optimization.

        Args:
            confidences: Raw confidences
            correct: Correctness labels
            scaled_confidences: Scaled confidences

        Returns:
            Gradient value
        """
        # Convert to logits
        logits = np.log(confidences / (1 - confidences + 1e-10))

        # Compute gradient
        n = len(confidences)

        grad = np.sum(
            (logits / self.temperature**2) * (scaled_confidences - correct)
        ) / n

        return grad

    def transform(self, confidences: np.ndarray) -> np.ndarray:
        """
        Apply temperature scaling to confidences.

        Args:
            confidences: Confidence scores to scale

        Returns:
            Scaled confidences
        """
        if not self.is_fitted:
            logger.warning("Scaler not fitted, returning raw confidences")
            return confidences

        return self._scale_confidences(confidences)

    def fit_transform(
        self,
        confidences: np.ndarray,
        correct: np.ndarray,
        **kwargs
    ) -> np.ndarray:
        """
        Fit and transform in one step.

        Args:
            confidences: Confidence scores
            correct: Correctness labels
            **kwargs: Additional arguments for fit()

        Returns:
            Scaled confidences
        """
        self.fit(confidences, correct, **kwargs)
        return self.transform(confidences)


def main():
    """Test the temperature scaling."""
    # Example data
    np.random.seed(42)
    n_samples = 1000

    # Generate synthetic confidences (overconfident)
    confidences = np.random.beta(3, 2, n_samples)
    confidences = np.clip(confidences + 0.1, 0.01, 0.99)

    # Generate correctness based on true probability
    true_probs = confidences * 0.8  # Model is overconfident
    correct = np.random.binomial(1, true_probs)

    # Split into train and test
    split = int(0.5 * n_samples)
    train_conf = confidences[:split]
    train_correct = correct[:split]
    test_conf = confidences[split:]
    test_correct = correct[split:]

    # Fit temperature scaling
    print("Fitting Temperature Scaling:")
    scaler = TemperatureScaling()
    scaler.fit(train_conf, train_correct)

    # Transform test confidences
    scaled_conf = scaler.transform(test_conf)

    # Compute calibration metrics
    def compute_ece(conf, corr, n_bins=10):
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(conf, bin_edges) - 1

        ece = 0.0
        total = len(conf)

        for i in range(n_bins):
            mask = bin_indices == i
            if np.sum(mask) == 0:
                continue

            accuracy = np.mean(corr[mask])
            avg_conf = np.mean(conf[mask])
            weight = np.sum(mask) / total
            ece += weight * abs(accuracy - avg_conf)

        return ece

    raw_ece = compute_ece(test_conf, test_correct)
    scaled_ece = compute_ece(scaled_conf, test_correct)

    print(f"  Temperature: {scaler.temperature:.4f}")
    print(f"  Raw ECE: {raw_ece:.4f}")
    print(f"  Scaled ECE: {scaled_ece:.4f}")
    print(f"  Improvement: {raw_ece - scaled_ece:.4f}")


if __name__ == "__main__":
    main()
