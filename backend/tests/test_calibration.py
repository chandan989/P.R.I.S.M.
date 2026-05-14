"""
P.R.I.S.M. Calibration Tests

Tests for conformal prediction, temperature scaling, and calibration metrics.
"""

import pytest
import numpy as np
from calibration import (
    ConformalPredictor,
    TemperatureScaler,
    CalibrationEvaluator,
    TemperatureScaling,
    expected_calibration_error,
    brier_score
)


class TestConformalPredictor:
    """Tests for ConformalPredictor."""

    def test_fit(self):
        """Test fitting conformal predictor."""
        predictor = ConformalPredictor(alpha=0.1)

        # Create calibration data
        calibration_data = [
            (0.8, True),
            (0.7, True),
            (0.6, True),
            (0.4, False),
            (0.3, False),
        ]

        predictor.fit(calibration_data)

        assert predictor.is_calibrated
        assert predictor.quantile > 0

    def test_predict(self):
        """Test prediction with conformal predictor."""
        predictor = ConformalPredictor(alpha=0.1)

        # Fit first
        calibration_data = [
            (0.8, True),
            (0.7, True),
            (0.6, True),
            (0.4, False),
            (0.3, False),
        ]
        predictor.fit(calibration_data)

        # Predict
        interval = predictor.predict(0.75)

        assert interval.lower_bound >= 0
        assert interval.upper_bound <= 1
        assert interval.coverage == 0.9
        assert not interval.is_ood

    def test_predict_ood(self):
        """Test prediction with OOD detection."""
        predictor = ConformalPredictor(alpha=0.1, ood_threshold=0.5)

        # Fit first
        calibration_data = [
            (0.8, True),
            (0.7, True),
            (0.6, True),
            (0.4, False),
            (0.3, False),
        ]
        predictor.fit(calibration_data)

        # Predict with high semantic distance
        interval = predictor.predict(0.75, semantic_distance=0.9)

        assert interval.is_ood

    def test_predict_uncalibrated(self):
        """Test prediction without calibration."""
        predictor = ConformalPredictor(alpha=0.1)

        # Don't fit
        interval = predictor.predict(0.75)

        # Should still return an interval
        assert interval.lower_bound >= 0
        assert interval.upper_bound <= 1


class TestTemperatureScaler:
    """Tests for TemperatureScaler."""

    def test_fit(self):
        """Test fitting temperature scaler."""
        scaler = TemperatureScaler()

        # Create synthetic data
        np.random.seed(42)
        logits = np.random.randn(100, 3)
        labels = np.random.randint(0, 3, 100)

        scaler.fit(logits, labels, max_iter=100)

        assert scaler.is_fitted
        assert scaler.temperature > 0

    def test_transform(self):
        """Test transforming logits."""
        scaler = TemperatureScaler()

        # Fit first
        np.random.seed(42)
        logits = np.random.randn(100, 3)
        labels = np.random.randint(0, 3, 100)
        scaler.fit(logits, labels, max_iter=100)

        # Transform
        probs = scaler.transform(logits)

        assert probs.shape == logits.shape
        assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-5)

    def test_transform_unfitted(self):
        """Test transforming without fitting."""
        scaler = TemperatureScaler()

        logits = np.random.randn(10, 3)
        probs = scaler.transform(logits)

        # Should still return probabilities
        assert probs.shape == logits.shape


class TestCalibrationEvaluator:
    """Tests for CalibrationEvaluator."""

    def test_evaluate(self):
        """Test evaluating calibration metrics."""
        evaluator = CalibrationEvaluator(n_bins=10)

        # Create synthetic data
        np.random.seed(42)
        confidences = np.random.beta(2, 2, 1000)
        correct = np.random.binomial(1, confidences)

        metrics = evaluator.evaluate(confidences, correct)

        assert metrics.ece >= 0
        assert metrics.brier_score >= 0
        assert len(metrics.reliability) > 0

    def test_ece_computation(self):
        """Test ECE computation."""
        np.random.seed(42)
        confidences = np.random.beta(2, 2, 1000)
        correct = np.random.binomial(1, confidences)

        ece = expected_calibration_error(confidences, correct, n_bins=10)

        assert 0 <= ece <= 1

    def test_brier_score_computation(self):
        """Test Brier score computation."""
        np.random.seed(42)
        confidences = np.random.beta(2, 2, 1000)
        correct = np.random.binomial(1, confidences)

        bs = brier_score(confidences, correct)

        assert 0 <= bs <= 1


class TestTemperatureScaling:
    """Tests for TemperatureScaling."""

    def test_fit(self):
        """Test fitting temperature scaling."""
        scaler = TemperatureScaling()

        # Create synthetic data
        np.random.seed(42)
        confidences = np.random.beta(2, 2, 1000)
        correct = np.random.binomial(1, confidences)

        scaler.fit(confidences, correct, max_iter=100)

        assert scaler.is_fitted
        assert scaler.temperature > 0

    def test_transform(self):
        """Test transforming confidences."""
        scaler = TemperatureScaling()

        # Fit first
        np.random.seed(42)
        confidences = np.random.beta(2, 2, 1000)
        correct = np.random.binomial(1, confidences)
        scaler.fit(confidences, correct, max_iter=100)

        # Transform
        scaled = scaler.transform(confidences)

        assert scaled.shape == confidences.shape
        assert np.all((scaled >= 0) & (scaled <= 1))

    def test_fit_transform(self):
        """Test fit and transform in one step."""
        scaler = TemperatureScaling()

        # Create synthetic data
        np.random.seed(42)
        confidences = np.random.beta(2, 2, 1000)
        correct = np.random.binomial(1, confidences)

        scaled = scaler.fit_transform(confidences, correct, max_iter=100)

        assert scaler.is_fitted
        assert scaled.shape == confidences.shape
