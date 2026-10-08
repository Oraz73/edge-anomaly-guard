"""Simple web interface for EdgeGuard.

Run:  streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from edgeguard import FEATURES, classification_report, generate_synthetic, get_detector
from edgeguard.benchmark import model_size_bytes, run_benchmark
from edgeguard.preprocess import clean
from edgeguard.visualize import plot_anomalies

HELP = {
    "precision": "Share of alarms that were real attacks",
    "recall": "Share of real attacks that were caught",
    "f1": "Overall score combining precision and recall",
}
METHODS = {"Robust Z-score (lightweight)": "zscore", "Isolation Forest (ML)": "iforest"}

st.set_page_config(page_title="EdgeGuard", page_icon="🛡️", layout="wide")
st.title("🛡️ EdgeGuard")
st.caption("Anomaly detection in smart city IoT telemetry for edge devices")

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("1. Data")
    source = st.radio("Source", ["Generate synthetic data", "Upload CSV"])
    if source == "Generate synthetic data":
        n = st.slider("Number of records", 500, 5000, 2000, step=500)
        ratio = st.slider("Share of attacks, %", 1, 15, 5) / 100
        seed = st.number_input("Random seed", value=42, step=1)
        uploaded = None
    else:
        uploaded = st.file_uploader("CSV with columns: " + ", ".join(FEATURES), type="csv")

    st.header("2. Method")
    method_label = st.selectbox("Detection method", list(METHODS))
    run = st.button("▶ Detect anomalies", type="primary", width="stretch")

# ---------------------------------------------------------------- data
if source == "Generate synthetic data":
    df = generate_synthetic(int(n), ratio, int(seed))
elif uploaded is not None:
    df = pd.read_csv(uploaded)
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        st.error("Missing columns: " + ", ".join(missing))
        st.stop()
    df = clean(df, FEATURES)
else:
    st.info("Upload a CSV file in the sidebar, or switch to synthetic data.")
    st.stop()

tab_detect, tab_compare, tab_data = st.tabs(["Detection", "Compare methods", "Data"])

# ---------------------------------------------------------------- detection
with tab_detect:
    if not run:
        st.info("Choose settings in the sidebar and press **Detect anomalies**.")
    else:
        x = df[FEATURES].to_numpy()
        detector = get_detector(METHODS[method_label]).fit(x)
        df["anomaly"] = detector.predict(x)

        c1, c2, c3 = st.columns(3)
        c1.metric("Records", len(df))
        c2.metric("Anomalies found", int(df["anomaly"].sum()))
        c3.metric("Model size", f"{model_size_bytes(detector) / 1024:.1f} KB")

        if "label" in df.columns:
            rep = classification_report(df["label"], df["anomaly"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Precision", f"{rep['precision']:.2f}", help=HELP["precision"])
            c2.metric("Recall", f"{rep['recall']:.2f}", help=HELP["recall"])
            c3.metric("F1", f"{rep['f1']:.2f}", help=HELP["f1"])

        png = plot_anomalies(df, FEATURES, df["anomaly"], "results/app_plot.png", method_label)
        st.image(str(png), caption="Red points are detected anomalies", width="stretch")

        st.subheader("Detected anomalies")
        st.dataframe(df[df["anomaly"] == 1], width="stretch", hide_index=True)
        st.download_button(
            "⬇ Download results (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "edgeguard_results.csv",
            "text/csv",
        )

# ---------------------------------------------------------------- comparison
with tab_compare:
    st.write("Both methods are trained on clean data and tested on data with attacks.")
    if st.button("Run comparison"):
        train = generate_synthetic(2000, 0.0, seed=1)
        test = generate_synthetic(2000, 0.05, seed=2)
        rows = []
        for label, name in METHODS.items():
            res = run_benchmark(
                get_detector(name),
                train[FEATURES].to_numpy(),
                test[FEATURES].to_numpy(),
                test["label"].to_numpy(),
            )
            rows.append(
                {
                    "Method": label,
                    "Precision": round(res["precision"], 2),
                    "Recall": round(res["recall"], 2),
                    "F1": round(res["f1"], 2),
                    "Latency, µs/record": round(res["latency_us_per_sample"], 2),
                    "Model size, KB": round(res["model_size_kb"], 1),
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.success("For edge devices, a lighter and faster model is preferred.")

# ---------------------------------------------------------------- raw data
with tab_data:
    st.dataframe(df.head(200), width="stretch", hide_index=True)
    st.caption(f"Showing first 200 of {len(df)} records")
