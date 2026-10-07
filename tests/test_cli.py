import json

import pandas as pd

from edgeguard.cli import main


def test_generate_detect_pipeline(tmp_path, capsys):
    data = tmp_path / "s.csv"
    out = tmp_path / "r.csv"
    plot = tmp_path / "p.png"
    assert main(["generate", "-o", str(data), "-n", "400"]) == 0
    args = ["detect", "-i", str(data), "-m", "zscore", "-o", str(out), "--plot", str(plot)]
    assert main(args) == 0
    result = pd.read_csv(out)
    assert {"anomaly", "score"} <= set(result.columns)
    assert plot.exists() and plot.stat().st_size > 0
    assert "Найдено аномалий" in capsys.readouterr().out


def test_benchmark_json(tmp_path):
    js = tmp_path / "b.json"
    assert main(["benchmark", "-n", "300", "--json", str(js)]) == 0
    rows = json.loads(js.read_text(encoding="utf-8"))
    assert {r["method"] for r in rows} == {"zscore", "iforest"}


def test_missing_file_returns_error_code(tmp_path, capsys):
    assert main(["detect", "-i", str(tmp_path / "none.csv")]) == 1
    assert "Ошибка" in capsys.readouterr().err
