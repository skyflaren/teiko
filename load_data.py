import csv
import os
import sqlite3

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "cell_data.db")
CSV_FILE = os.path.join(DATA_DIR, "cell-count.csv")


def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Subjects - response can be NULL
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            condition TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            treatment TEXT NOT NULL,
            response TEXT
        );
    """
    )

    # Samples
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS samples (
            sample_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            sample_type TEXT NOT NULL,
            time_from_treatment_start INTEGER NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
        );
    """
    )

    # Cell Counts Per Sample
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cell_counts (
            sample_id TEXT PRIMARY KEY,
            b_cell INTEGER NOT NULL,
            cd8_t_cell INTEGER NOT NULL,
            cd4_t_cell INTEGER NOT NULL,
            nk_cell INTEGER NOT NULL,
            monocyte INTEGER NOT NULL,
            FOREIGN KEY (sample_id) REFERENCES samples (sample_id)
        );
    """
    )
    conn.commit()


def load_data(conn, csv_filepath):
    if not os.path.exists(csv_filepath):
        raise FileNotFoundError(f"File not found at: {csv_filepath}")

    cursor = conn.cursor()
    with open(csv_filepath, mode="r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            raw_response = row["response"].strip() if row["response"] else None
            clean_response = None if (raw_response is None or raw_response.lower() in ("", "nan", "null", "none")) else raw_response
            
            # Subjects
            cursor.execute(
                """
                INSERT OR IGNORE INTO subjects 
                (subject_id, project, condition, age, sex, treatment, response)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    row["subject"],
                    row["project"],
                    row["condition"],
                    int(row["age"]),
                    row["sex"],
                    row["treatment"],
                    clean_response,
                ),
            )

            # Samples
            cursor.execute(
                """
                INSERT OR REPLACE INTO samples 
                (sample_id, subject_id, sample_type, time_from_treatment_start)
                VALUES (?, ?, ?, ?);
            """,
                (
                    row["sample"],
                    row["subject"],
                    row["sample_type"],
                    int(row["time_from_treatment_start"]),
                ),
            )

            # Cell Counts Per Sample
            cursor.execute(
                """
                INSERT OR REPLACE INTO cell_counts 
                (sample_id, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte)
                VALUES (?, ?, ?, ?, ?, ?);
            """,
                (
                    row["sample"],
                    int(row["b_cell"]),
                    int(row["cd8_t_cell"]),
                    int(row["cd4_t_cell"]),
                    int(row["nk_cell"]),
                    int(row["monocyte"]),
                ),
            )
    conn.commit()



os.makedirs(DATA_DIR, exist_ok=True)
conn = sqlite3.connect(DB_FILE)
try:
    init_db(conn)
    load_data(conn, CSV_FILE)
    print(f"Successfully loaded data from {CSV_FILE} into {DB_FILE}")
finally:
    conn.close()