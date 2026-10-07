"""Предобработка данных: очистка и нормализация признаков.

Нормализатор реализован на NumPy без лишних зависимостей, чтобы его можно
было перенести на устройство с минимальным окружением.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Удалить дубликаты, строки с пропусками и бесконечностями в признаках."""
    out = df.drop_duplicates().copy()
    out[features] = out[features].replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=features)
    return out.reset_index(drop=True)


class StandardScaler:
    """Стандартизация признаков: (x - mean) / std."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, x: np.ndarray) -> StandardScaler:
        x = np.asarray(x, dtype=float)
        if x.ndim != 2 or x.shape[0] == 0:
            raise ValueError("Ожидается непустая двумерная матрица признаков")
        self.mean_ = x.mean(axis=0)
        std = x.std(axis=0)
        self.std_ = np.where(std == 0, 1.0, std)  # защита от деления на ноль
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.std_ is None:
            raise RuntimeError("Сначала вызовите fit()")
        return (np.asarray(x, dtype=float) - self.mean_) / self.std_

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        return self.fit(x).transform(x)
