import streamlit as st
import pandas as pd
import glob
import json

st.set_page_config(page_title="RAG Evaluation Dashboard", layout="wide")

st.title("📊 RAGAS Evaluation Dashboard")

report_files = sorted(glob.glob("evaluation/reports/evaluation_*.json"), reverse=True)

if not report_files:
    st.info(
        "No evaluation reports found. Run `uv run python evaluation/evaluate.py` to create one."
    )
else:
    selected_report = st.selectbox("Select Evaluation Report Run", report_files)

    with open(selected_report, "r") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # 1. Summary Metrics Display
    st.subheader("📈 Overall Pipeline Scores")
    cols = st.columns(5)
    metric_cols = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "answer_correctness",
    ]

    for col, m in zip(cols, metric_cols):
        if m in df.columns:
            avg_val = df[m].mean()
            col.metric(m.replace("_", " ").title(), f"{avg_val:.2%}")

    st.markdown("---")

    # 2. Failure Analysis Section
    st.subheader("🔍 Query Weakness & Failure Analysis")
    metric_filter = st.selectbox(
        "Sort by metric (ascending to highlight lowest scores):", metric_cols
    )

    if metric_filter in df.columns:
        worst_queries = df.sort_values(by=metric_filter, ascending=True)
        st.dataframe(
            worst_queries[["question", "answer", "ground_truth", metric_filter]],
            use_container_width=True,
        )

    # 3. Full Data Table
    st.subheader("📄 Raw Evaluation Dataset")
    st.dataframe(df, use_container_width=True)
