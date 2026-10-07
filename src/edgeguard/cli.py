"""Интерфейс командной строки ``edgeguard``.

Примеры::

    edgeguard generate -o data/sample.csv
    edgeguard detect -i data/sample.csv -m iforest -o results.csv --plot plot.png
    edgeguard benchmark
"""

from __future__ import annotations

import argparse
import json
import sys

from edgeguard import __version__
from edgeguard.benchmark import run_benchmark
from edgeguard.data import FEATURES, LABEL, generate_synthetic, load_csv
from edgeguard.detectors import DETECTORS, get_detector
from edgeguard.metrics import classification_report
from edgeguard.preprocess import clean


def _cmd_generate(args: argparse.Namespace) -> int:
    df = generate_synthetic(args.samples, args.anomaly_ratio, args.seed)
    df.to_csv(args.output, index=False)
    print(f"Сохранено {len(df)} строк в {args.output}")
    return 0


def _cmd_detect(args: argparse.Namespace) -> int:
    df = clean(load_csv(args.input), FEATURES)
    x = df[FEATURES].to_numpy()
    detector = get_detector(args.method).fit(x)
    df["anomaly"] = detector.predict(x)
    df["score"] = detector.score(x)
    print(f"Найдено аномалий: {int(df['anomaly'].sum())} из {len(df)}")

    if LABEL in df.columns:
        report = classification_report(df[LABEL], df["anomaly"])
        print(json.dumps({k: round(v, 4) for k, v in report.items()}, ensure_ascii=False))
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Результат сохранён в {args.output}")
    if args.plot:
        from edgeguard.visualize import plot_anomalies

        plot_anomalies(df, FEATURES, df["anomaly"], args.plot, f"Метод: {args.method}")
        print(f"График сохранён в {args.plot}")
    return 0


def _cmd_benchmark(args: argparse.Namespace) -> int:
    train = generate_synthetic(args.samples, 0.0, seed=1)  # «чистый» период
    test = generate_synthetic(args.samples, 0.05, seed=2)
    rows = []
    for name in DETECTORS:
        res = run_benchmark(
            get_detector(name),
            train[FEATURES].to_numpy(),
            test[FEATURES].to_numpy(),
            test[LABEL].to_numpy(),
        )
        rows.append({"method": name, **{k: round(v, 4) for k, v in res.items()}})

    header = ["method", "precision", "recall", "f1", "latency_us_per_sample", "model_size_kb"]
    print(" | ".join(header))
    for r in rows:
        print(" | ".join(str(r[h]) for h in header))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="edgeguard",
        description="Обнаружение аномалий в телеметрии IoT-устройств умного города",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="создать синтетический набор данных")
    g.add_argument("-o", "--output", default="sample.csv")
    g.add_argument("-n", "--samples", type=int, default=2000)
    g.add_argument("-r", "--anomaly-ratio", type=float, default=0.05)
    g.add_argument("--seed", type=int, default=42)
    g.set_defaults(func=_cmd_generate)

    d = sub.add_parser("detect", help="найти аномалии в CSV-файле")
    d.add_argument("-i", "--input", required=True)
    d.add_argument("-m", "--method", choices=list(DETECTORS), default="iforest")
    d.add_argument("-o", "--output")
    d.add_argument("--plot", help="путь для PNG-графика")
    d.set_defaults(func=_cmd_detect)

    b = sub.add_parser("benchmark", help="сравнить методы по точности и ресурсам")
    b.add_argument("-n", "--samples", type=int, default=2000)
    b.add_argument("--json", help="сохранить результаты в JSON")
    b.set_defaults(func=_cmd_benchmark)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
