"""Загрузка данных и генерация синтетического набора телеметрии IoT-узла.

Синтетические данные имитируют сетевую телеметрию шлюза умного города
(например, контроллера уличного освещения или камеры). Нормальный трафик
имеет суточную периодичность, а аномалии моделируют три типа событий:

* ``ddos``   — резкий рост числа пакетов и объёма трафика;
* ``scan``   — сканирование портов: много соединений при малом объёме;
* ``hijack`` — захват устройства: высокая загрузка CPU при обычном трафике.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FEATURES: list[str] = ["packets_per_sec", "bytes_per_sec", "conn_count", "cpu_load"]
LABEL = "label"
ATTACK_TYPES = ("ddos", "scan", "hijack")


def generate_synthetic(
    n_samples: int = 2000,
    anomaly_ratio: float = 0.05,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Сгенерировать синтетический временной ряд телеметрии с размеченными аномалиями.

    Parameters
    ----------
    n_samples:
        Количество наблюдений (по одному в минуту).
    anomaly_ratio:
        Доля аномальных наблюдений, от 0 до 0.5.
    seed:
        Зерно генератора случайных чисел для воспроизводимости.

    Returns
    -------
    pandas.DataFrame
        Столбцы ``timestamp``, признаки из :data:`FEATURES`, ``label`` (0/1)
        и ``attack_type`` (``normal`` или тип атаки).
    """
    if n_samples <= 0:
        raise ValueError("n_samples должно быть положительным")
    if not 0.0 <= anomaly_ratio <= 0.5:
        raise ValueError("anomaly_ratio должно быть в диапазоне [0, 0.5]")

    rng = np.random.default_rng(seed)
    t = np.arange(n_samples)
    daily = 1.0 + 0.5 * np.sin(2 * np.pi * t / 1440.0)  # суточный цикл

    packets = rng.normal(200.0, 20.0, n_samples) * daily
    bytes_ = packets * rng.normal(500.0, 30.0, n_samples)
    conns = rng.poisson(15, n_samples).astype(float) * daily
    cpu = np.clip(rng.normal(30.0, 5.0, n_samples), 0.0, 100.0)

    label = np.zeros(n_samples, dtype=int)
    attack = np.full(n_samples, "normal", dtype=object)

    n_anom = int(round(n_samples * anomaly_ratio))
    idx = rng.choice(n_samples, size=n_anom, replace=False)
    kinds = rng.choice(ATTACK_TYPES, size=n_anom)
    for i, kind in zip(idx, kinds, strict=True):
        if kind == "ddos":
            packets[i] *= rng.uniform(2.5, 6.0)
            bytes_[i] *= rng.uniform(2.5, 6.0)
        elif kind == "scan":
            conns[i] *= rng.uniform(3.0, 8.0)
            bytes_[i] *= 0.5
        else:  # hijack
            cpu[i] = rng.uniform(55.0, 95.0)
        label[i] = 1
        attack[i] = kind

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n_samples, freq="min"),
            "packets_per_sec": packets,
            "bytes_per_sec": bytes_,
            "conn_count": conns,
            "cpu_load": cpu,
            LABEL: label,
            "attack_type": attack,
        }
    )


def load_csv(path: str | Path, features: list[str] | None = None) -> pd.DataFrame:
    """Загрузить CSV-файл и проверить наличие нужных столбцов-признаков."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    df = pd.read_csv(path)
    required = features or FEATURES
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"В файле нет столбцов: {', '.join(missing)}")
    return df
