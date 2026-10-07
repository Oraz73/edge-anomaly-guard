"""Оценка пригодности детектора для edge-устройства.

Помимо точности, на периферийном устройстве важны время обучения,
задержка обработки одного наблюдения и размер модели в памяти.
"""

from __future__ import annotations

import pickle
import time

import numpy as np

from edgeguard.detectors import BaseDetector
from edgeguard.metrics import classification_report


def model_size_bytes(detector: BaseDetector) -> int:
    """Размер сериализованной модели в байтах (оценка объёма для хранения)."""
    return len(pickle.dumps(detector))


def run_benchmark(
    detector: BaseDetector,
    x_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    repeats: int = 3,
) -> dict[str, float]:
    """Обучить детектор и измерить качество и ресурсы.

    Задержка считается как медиана по ``repeats`` прогонам, делённая
    на число наблюдений, — это время обработки одной записи телеметрии.
    """
    t0 = time.perf_counter()
    detector.fit(x_train)
    fit_time = time.perf_counter() - t0

    timings = []
    y_pred = None
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter()
        y_pred = detector.predict(x_test)
        timings.append(time.perf_counter() - t0)

    result = classification_report(y_test, y_pred)
    result.update(
        {
            "fit_time_s": fit_time,
            "latency_us_per_sample": float(np.median(timings)) / len(x_test) * 1e6,
            "model_size_kb": model_size_bytes(detector) / 1024,
        }
    )
    return result
