import os
import sqlite3
import pandas as pd
from scipy import stats

DB_FILE = os.path.join("data", "cell_data.db")

def process_and_save():
    conn = sqlite3.connect(DB_FILE)

    subjects_df = pd.read_sql_query("SELECT * FROM subjects", conn)
    samples_df = pd.read_sql_query("SELECT * FROM samples", conn)
    counts_df = pd.read_sql_query("SELECT * FROM cell_counts", conn)

    df_all = subjects_df.merge(samples_df, on="subject_id").merge(counts_df, on="sample_id").rename(columns={"sample_id": "sample"})
    cell_cols = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    df_all["total_count"] = df_all[cell_cols].sum(axis=1)
    
    df_long = pd.melt(
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
    df_long["percentage"] = (df_long["count"] / df_long["total_count"])*100
    df_long.to_sql("summary_frequencies", conn, if_exists="replace", index=False)

    p3_mask = (
        (df_long["condition"].str.lower() == "melanoma")
        & (df_long["treatment"].str.lower() == "miraclib")
        & (df_long["sample_type"].str.upper() == "PBMC")
        & (df_long["response"].str.lower().isin(["yes", "no"]))
    )
    df_part3 = df_long[p3_mask]
    stats_results = []
    custom_order = ["b_cell", "cd4_t_cell", "cd8_t_cell", "monocyte", "nk_cell"]

    for pop in custom_order:
        pop_data = df_part3[df_part3["population"] == pop]
        resp = pop_data[pop_data["response"].str.lower() == "yes"]["percentage"]
        non_resp = pop_data[pop_data["response"].str.lower() == "no"]["percentage"]

        if len(resp) > 0 and len(non_resp) > 0:
            stat, p_val = stats.mannwhitneyu(resp, non_resp, alternative="two-sided")
            is_sig = p_val < 0.05
        else:
            stat, p_val, is_sig = 0, 1.0, False

        stats_results.append({
            "Population": pop,
            "Responders Mean (%)": round(resp.mean(), 2) if len(resp) else 0.0,
            "Non-Responders Mean (%)": (round(non_resp.mean(), 2) if len(non_resp) else 0.0),
            "U-Statistic": round(stat, 2),
            "p_value": float(p_val),
            "Significant (p < 0.05)": "Yes" if is_sig else "No",
        })

    stats_df = pd.DataFrame(stats_results)
    stats_df.to_sql("stats_results", conn, if_exists="replace", index=False)
    df_all.to_sql("df_processed_wide", conn, if_exists="replace", index=False)
    conn.close()
    print("Analysis saved to database!")


if __name__ == "__main__":
    process_and_save()