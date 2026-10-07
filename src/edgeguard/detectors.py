"""Детекторы аномалий с единым интерфейсом ``fit`` / ``score`` / ``predict``.

* :class:`ZScoreDetector` — статистический порог, почти нулевые требования
  к памяти и вычислениям; базовый вариант для самых слабых устройств.
* :class:`IsolationForestDetector` — ансамбль изолирующих деревьев
  (scikit-learn); точнее на многомерных аномалиях, но тяжелее.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from sklearn.ensemble import IsolationForest

from edgeguard.preprocess import StandardScaler


class BaseDetector(ABC):
    """Общий интерфейс детектора. ``predict`` возвращает 1 для аномалии."""

    def __init__(self) -> None:
        self.scaler = StandardScaler()
        self._fitted = False

    def fit(self, x: np.ndarray) -> BaseDetector:
        z = self.scaler.fit_transform(x)
        self._fit(z)
        self._fitted = True
        return self

    def score(self, x: np.ndarray) -> np.ndarray:
        """Оценка аномальности: чем больше, тем подозрительнее."""
        if not self._fitted:
            raise RuntimeError("Детектор не обучен: вызовите fit()")
        return self._score(self.scaler.transform(x))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.score(x) > self.threshold_).astype(int)

    @property
    @abstractmethod
    def threshold_(self) -> float: ...

    @abstractmethod
    def _fit(self, z: np.ndarray) -> None: ...

    @abstractmethod
    def _score(self, z: np.ndarray) -> np.ndarray: ...


class ZScoreDetector(BaseDetector):
    """Аномалия, если хотя бы один признак отклоняется более чем на ``k`` сигм.

    Для устойчивости к выбросам в обучающих данных используется медиана
    и MAD (медианное абсолютное отклонение) вместо среднего и std.
    """

    def __init__(self, k: float = 4.0) -> None:
        super().__init__()
        if k <= 0:
            raise ValueError("k должно быть положительным")
        self.k = k
        self.median_: np.ndarray | None = None
        self.mad_: np.ndarray | None = None

    @property
    def threshold_(self) -> float:
        return self.k

    def _fit(self, z: np.ndarray) -> None:
        self.median_ = np.median(z, axis=0)
        mad = np.median(np.abs(z - self.median_), axis=0) * 1.4826
        self.mad_ = np.where(mad == 0, 1.0, mad)

    def _score(self, z: np.ndarray) -> np.ndarray:
        return np.max(np.abs(z - self.median_) / self.mad_, axis=1)


class IsolationForestDetector(BaseDetector):
    """Обёртка над :class:`sklearn.ensemble.IsolationForest`."""

    def __init__(
        self,
        n_estimators: int = 50,
        contamination: float = 0.02,
        random_state: int | None = 42,
    ) -> None:
        super().__init__()
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
        )

    @property
    def threshold_(self) -> float:
        return 0.0

    def _fit(self, z: np.ndarray) -> None:
        self.model.fit(z)

    def _score(self, z: np.ndarray) -> np.ndarray:
        # decision_function < 0 означает аномалию; меняем знак.
        return -self.model.decision_function(z)


DETECTORS = {"zscore": ZScoreDetector, "iforest": IsolationForestDetector}


def get_detector(name: str, **kwargs) -> BaseDetector:
    """Создать детектор по имени: ``zscore`` или ``iforest``."""
    try:
        return DETECTORS[name](**kwargs)
    except KeyError:
        raise ValueError(f"Неизвестный метод '{name}'. Доступны: {', '.join(DETECTORS)}") from None
