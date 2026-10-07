import pandas as pd
import pytest

from edgeguard.data import FEATURES, generate_synthetic, load_csv


def test_generate_shape_and_columns():
    df = generate_synthetic(500, 0.1, seed=0)
    assert len(df) == 500
    for col in FEATURES + ["timestamp", "label", "attack_type"]:
        assert col in df.columns


def test_anomaly_ratio_is_respected():
    df = generate_synthetic(1000, 0.05, seed=0)
    assert df["label"].sum() == 50
    assert set(df.loc[df["label"] == 1, "attack_type"]) <= {"ddos", "scan", "hijack"}


def test_generation_is_reproducible():
    a = generate_synthetic(200, seed=7)
    b = generate_synthetic(200, seed=7)
    pd.testing.assert_frame_equal(a, b)


@pytest.mark.parametrize("n, ratio", [(0, 0.05), (100, -0.1), (100, 0.9)])
def test_invalid_arguments(n, ratio):
    with pytest.raises(ValueError):
        generate_synthetic(n, ratio)


def test_load_csv_roundtrip(tmp_path):
    path = tmp_path / "d.csv"
    generate_synthetic(100).to_csv(path, index=False)
    assert len(load_csv(path)) == 100


def test_load_csv_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_csv(tmp_path / "nope.csv")


def test_load_csv_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"a": [1, 2]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="нет столбцов"):
        load_csv(path)
