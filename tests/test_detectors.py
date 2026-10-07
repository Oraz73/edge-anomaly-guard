import numpy as np
import pytest

from edgeguard.data import FEATURES, generate_synthetic
from edgeguard.detectors import IsolationForestDetector, ZScoreDetector, get_detector
from edgeguard.metrics import classification_report


@pytest.fixture(scope="module")
def dataset():
    train = generate_synthetic(2000, 0.0, seed=1)
    test = generate_synthetic(2000, 0.05, seed=2)
    return train[FEATURES].to_numpy(), test[FEATURES].to_numpy(), test["label"].to_numpy()


@pytest.mark.parametrize("name", ["zscore", "iforest"])
def test_detector_finds_most_attacks(dataset, name):
    x_train, x_test, y_test = dataset
    pred = get_detector(name).fit(x_train).predict(x_test)
    report = classification_report(y_test, pred)
    assert report["recall"] >= 0.7, report
    assert report["f1"] >= 0.5, report


@pytest.mark.parametrize("cls", [ZScoreDetector, IsolationForestDetector])
def test_predict_output_is_binary(dataset, cls):
    x_train, x_test, _ = dataset
    pred = cls().fit(x_train).predict(x_test)
    assert pred.shape == (len(x_test),)
    assert set(np.unique(pred)) <= {0, 1}


def test_obvious_outlier_scores_higher(dataset):
    x_train, _, _ = dataset
    det = ZScoreDetector().fit(x_train)
    normal = x_train[:1]
    outlier = normal * np.array([10, 10, 1, 1])
    assert det.score(outlier)[0] > det.score(normal)[0]
    assert det.predict(outlier)[0] == 1


def test_unfitted_detector_raises():
    with pytest.raises(RuntimeError):
        ZScoreDetector().predict(np.zeros((1, 4)))


def test_invalid_k():
    with pytest.raises(ValueError):
        ZScoreDetector(k=0)


def test_unknown_method():
    with pytest.raises(ValueError, match="Неизвестный метод"):
        get_detector("svm")
