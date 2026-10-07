import numpy as np
import pandas as pd
import pytest

from edgeguard.preprocess import StandardScaler, clean


def test_clean_removes_nan_inf_and_duplicates():
    df = pd.DataFrame({"a": [1.0, 1.0, np.nan, np.inf, 5.0], "b": [1, 1, 2, 3, 4]})
    out = clean(df, ["a"])
    assert out["a"].tolist() == [1.0, 5.0]


def test_scaler_zero_mean_unit_std():
    x = np.random.default_rng(0).normal(10, 3, size=(500, 3))
    z = StandardScaler().fit_transform(x)
    np.testing.assert_allclose(z.mean(axis=0), 0, atol=1e-9)
    np.testing.assert_allclose(z.std(axis=0), 1, atol=1e-9)


def test_scaler_constant_column_no_division_by_zero():
    x = np.array([[1.0, 5.0], [2.0, 5.0], [3.0, 5.0]])
    z = StandardScaler().fit_transform(x)
    assert np.all(np.isfinite(z))
    assert np.all(z[:, 1] == 0)


def test_scaler_requires_fit():
    with pytest.raises(RuntimeError):
        StandardScaler().transform([[1.0]])


def test_scaler_rejects_bad_input():
    with pytest.raises(ValueError):
        StandardScaler().fit(np.array([1.0, 2.0]))
