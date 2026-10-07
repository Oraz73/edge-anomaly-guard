"""Визуализация временного ряда с отмеченными аномалиями."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # работа без дисплея (сервер, CI, edge-устройство)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def plot_anomalies(
    df: pd.DataFrame,
    features: list[str],
    predicted: np.ndarray,
    output: str | Path,
    title: str = "Обнаруженные аномалии",
) -> Path:
    """Построить графики признаков и отметить найденные аномалии красным.

    Сохраняет PNG-файл и возвращает путь к нему.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    predicted = np.asarray(predicted).astype(bool)
    df = df.reset_index(drop=True)
    if "timestamp" in df.columns:
        x = pd.to_datetime(df["timestamp"])  # после чтения CSV это строки
    else:
        x = pd.Series(np.arange(len(df)))

    fig, axes = plt.subplots(len(features), 1, figsize=(10, 2.2 * len(features)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, feat in zip(axes, features, strict=True):
        ax.plot(x, df[feat], lw=0.6, color="#4C72B0", label="данные")
        ax.scatter(
            x.to_numpy()[predicted],
            df[feat].to_numpy()[predicted],
            s=12,
            color="#C44E52",
            label="аномалия",
            zorder=3,
        )
        ax.set_ylabel(feat, fontsize=8)
        ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    axes[0].legend(loc="upper right", fontsize=8)
    axes[0].set_title(title)
    fig.tight_layout()
    fig.savefig(output, dpi=120)
    plt.close(fig)
    return output
