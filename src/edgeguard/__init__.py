"""EdgeGuard — лёгкий модуль обнаружения аномалий в данных IoT-устройств
умного города, рассчитанный на работу на периферийных (edge) устройствах.
"""

from edgeguard.data import FEATURES, generate_synthetic, load_csv
from edgeguard.detectors import IsolationForestDetector, ZScoreDetector, get_detector
from edgeguard.metrics import classification_report
from edgeguard.preprocess import StandardScaler, clean

__all__ = [
    "FEATURES",
    "IsolationForestDetector",
    "StandardScaler",
    "ZScoreDetector",
    "classification_report",
    "clean",
    "generate_synthetic",
    "get_detector",
    "load_csv",
]

__version__ = "0.1.0"
