import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as bg
from scipy import stats
import streamlit as st


st.set_page_config(page_title="Cell Count Clinical Trial Dashboard", layout="wide")

@st.cache_data
def load_all_data():
    DB_FILE = os.path.join("data", "cell_data.db")
    conn = sqlite3.connect(DB_FILE)
    subjects_df = pd.read_sql_query("SELECT * FROM subjects", conn)
    samples_df = pd.read_sql_query("SELECT * FROM samples", conn)
    counts_df = pd.read_sql_query("SELECT * FROM cell_counts", conn)
    conn.close()

    df_all = (
        subjects_df.merge(samples_df, on="subject_id")
        .merge(counts_df, on="sample_id")
        .rename(columns={"sample_id": "sample"})
    )
    cell_cols = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    df_all["total_count"] = df_all[cell_cols].sum(axis=1)

    return df_all, cell_cols


# Load data
df_all, cell_cols = load_all_data()
st.title("Clinical Trial Cell Population Dashboard")
st.markdown("Interactive analysis of patient response and cell frequencies")

df_long_all = pd.melt(
    df_all,
    id_vars=[
        "sample",
        "subject_id",
        "response",
        "sex",
        "total_count",
        "time_from_treatment_start",
        "project",
        "condition",
        "treatment",
        "sample_type",
    ],
    value_vars=cell_cols,
    var_name="population",
    value_name="count",
)
df_long_all["percentage"] = (df_long_all["count"] / df_long_all["total_count"])*100

mask_all = (
    (df_all["condition"].str.lower() == "melanoma") &
    (df_all["treatment"].str.lower() == "miraclib") &
    (df_all["sample_type"].str.upper() == "PBMC")
)

mask_long = (
    (df_long_all["condition"].str.lower() == "melanoma") &
    (df_long_all["treatment"].str.lower() == "miraclib") &
    (df_long_all["sample_type"].str.upper() == "PBMC")
)

tab1, tab2, tab3, tab4 = st.tabs(["Part 2: Relative Frequencies", "Part 3: Statistical Comparison", "Part 4: Baseline Cohort", "Bonus"])


# TAB 1: Summary & Relative Frequencies (Part 2)
with tab1:
    st.header("Cell Population Summary Table (All Samples)")
    st.metric("Total Samples Loaded", df_all["sample"].nunique())

    summary_table = (
        df_long_all[["sample", "total_count", "population", "count", "percentage"]]
        .sort_values(by=["sample", "population"])
        .reset_index(drop=True)
    )
    st.dataframe(summary_table, use_container_width=True, height=300)
    st.subheader("Cell Composition Distribution Across Samples")
    fig_stack = px.bar(
        df_long_all,
        x="sample",
        y="percentage",
        color="population",
        title="Cell Type Percentage Composition Per Sample",
        labels={"percentage": "Relative Frequency (%)", "sample": "Sample ID"},
    )
    st.plotly_chart(fig_stack, use_container_width=True)


# TAB 2: Statistical Comparison (Part 3)
with tab2:
    st.header(f"Statistical Comparison (Melanoma, Miraclib, PBMC)")
    p3_mask = mask_long & df_long_all["response"].str.lower().isin(["yes", "no"])
    df_part3 = df_long_all[p3_mask].copy()
    
    custom_order, results = ["b_cell", "cd4_t_cell", "cd8_t_cell", "monocyte", "nk_cell"], []

    for pop in custom_order:
        pop_data = df_part3[df_part3["population"] == pop]
        responders = pop_data[pop_data["response"].str.lower() == "yes"]["percentage"]
        non_responders = pop_data[pop_data["response"].str.lower() == "no"]["percentage"]

        if len(responders) > 0 and len(non_responders) > 0:
            stat, p_val = stats.mannwhitneyu(responders, non_responders, alternative="two-sided")
            is_sig = p_val < 0.05
        else:
            stat, p_val, is_sig = 0, 1.0, False

        results.append({
                "Population": pop,
                "Responders Mean (%)": round(responders.mean(), 2),
                "Non-Responders Mean (%)": round(non_responders.mean(), 2),
                "U-Statistic": round(stat, 2),
                "p-value": f"{p_val:.4e}",
                "Significant (p < 0.05)": "Yes" if is_sig else "No",
        })

    stats_df = pd.DataFrame(results)
    st.subheader("Mann-Whitney U Test Results")
    st.table(stats_df)
   
    sig_pops = stats_df[stats_df["Significant (p < 0.05)"] == "Yes"]["Population"].tolist()
    if sig_pops:
        st.success(f"**Statistically Significant Populations (p < 0.05):** {', '.join(sig_pops)}")
    else:
        st.info("No cell populations showed a statistically significant difference at p < 0.05.")

    st.subheader("Population Relative Frequencies: Responders vs. Non-Responders")
    fig_box = px.box(
        df_part3,
        x="population",
        y="percentage",
        color="response",
        category_orders={"population": custom_order},
        color_discrete_map={"yes": "#73c796", "no": "#e05a70"},
        points="all",
        title="Cell Population Relative Frequencies (Melanoma | Miraclib | PBMC)",
        labels={
            "percentage": "Relative Frequency (%)",
            "population": "Immune Cell Population",
            "response": "Response",
        },
    )
    st.plotly_chart(fig_box, use_container_width=True)


# TAB 3: Baseline Subsets (Part 4)
with tab3:
    st.header("Baseline Cohort (Time=0)")
    p4_mask = mask_all & (df_all["time_from_treatment_start"] == 0)
    baseline_df = df_all[p4_mask].copy()
    unique_subjects = baseline_df.drop_duplicates(subset=["subject_id"])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("Samples per Project")
        st.dataframe(baseline_df["project"].value_counts())
    with c2:
        st.write("Responders vs Non-Responders")
        st.dataframe(unique_subjects["response"].value_counts())
    with c3:
        st.write("Males vs Females")
        st.dataframe(unique_subjects["sex"].value_counts())

# TAB 4: Bonus
with tab4:
    st.subheader("Bonus: Average B Cell Counts for Melanoma Male Responders at Time=0")

    bonus_mask = (
        (df_all["condition"].str.lower() == "melanoma") &
        (df_all["sex"].str.upper() == "M") &
        (df_all["response"].str.lower() == "yes") &
        (df_all["time_from_treatment_start"] == 0)
    )
    bonus_df = df_all[bonus_mask]
    avg_b_cells = bonus_df["b_cell"].mean()
    col_metric, col_table = st.columns([1, 2])

    with col_metric:
        st.metric(label="Average B-Cell Count", value=f"{avg_b_cells:.2f}" if pd.notna(avg_b_cells) else "N/A",)
        st.caption("Filter Criteria: Condition = Melanoma | Sex = Male | Response = Responded ('yes') | Time = 0")

    with col_table:
        st.write("**Matching Patient Samples**")
        st.dataframe(bonus_df[["subject_id", "sample", "treatment", "sample_type", "b_cell", "total_count"]], use_container_width=True)