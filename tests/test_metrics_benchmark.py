import numpy as np
import pytest
from sklearn.metrics import f1_score, precision_score, recall_score

from edgeguard.benchmark import model_size_bytes, run_benchmark
from edgeguard.data import FEATURES, generate_synthetic
from edgeguard.detectors import ZScoreDetector
from edgeguard.metrics import classification_report, confusion


def test_confusion_counts():
    assert confusion([1, 0, 1, 0], [1, 1, 0, 0]) == (1, 1, 1, 1)


def test_report_matches_sklearn():
    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, 300)
    y_pred = rng.integers(0, 2, 300)
    rep = classification_report(y_true, y_pred)
    assert rep["precision"] == pytest.approx(precision_score(y_true, y_pred))
    assert rep["recall"] == pytest.approx(recall_score(y_true, y_pred))
    assert rep["f1"] == pytest.approx(f1_score(y_true, y_pred))


def test_report_no_positive_predictions():
    rep = classification_report([0, 1], [0, 0])
    assert rep["precision"] == 0.0 and rep["f1"] == 0.0


def test_shape_mismatch():
    with pytest.raises(ValueError):
        confusion([1, 0], [1])


def test_benchmark_returns_resource_metrics():
    train = generate_synthetic(500, 0.0, seed=1)
    test = generate_synthetic(500, 0.05, seed=2)
    res = run_benchmark(
        ZScoreDetector(),
        train[FEATURES].to_numpy(),
        test[FEATURES].to_numpy(),
        test["label"].to_numpy(),
        repeats=2,
    )
    for key in ("f1", "fit_time_s", "latency_us_per_sample", "model_size_kb"):
        assert key in res and res[key] >= 0


def test_zscore_model_is_tiny():
    det = ZScoreDetector().fit(generate_synthetic(500)[FEATURES].to_numpy())
    assert model_size_bytes(det) < 10 * 1024  # меньше 10 КБ — подходит для микроконтроллера
