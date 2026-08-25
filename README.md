# Clinical Trial Cell Population Analysis & Dashboard

Link to deployment: [https://justinlu-teiko.streamlit.app/](https://justinlu-teiko.streamlit.app/)

## Setup Instructions

This project runs automatically via GitHub Codespaces using the provided `Makefile`, which installs dependencies, sets up the database, performs the analysis, and generates an interactive dashboard.

```bash
make setup
make pipeline
make dashboard
```

## Database
The database is in the following schema:

**subjects** - patient demographics
> - subject_id [PK]
> - project
> - condition
> - age
> - sex
> - treatment
> - response

**samples** - sample details
> - sample_id [PK]
> - subject_id [FK]
> - sample_type
> - time_from_treatment_start

**cell_counts** - raw cell population counts
> - sample_id [PK/FK]
> - b_cell
> - cd4_t_cell
> - cd8_t_cell
> - nk_cell
> - monocyte

This was the logical separation allowing it to be designed in 3NF, with data pertaining to `subjects` and `samples` to be split and separating cell counts to prevent `samples` from being too large. Note: `response` in `subjects` is permitted to be null, as it follows that subjects not given treatments did not have a response.

Looking into the future, if patient or sample details need to be updated, this allows for quick, small adjustments to one row instead of many. When scaling to handle much more data and still perform analytics, we could create indices on columns like `condition` or `time_from_treatment_start` to optimize query performance, provided we don't need to update often. We could also migrate to a diferent database engine like PostgresQL to handle larger data flows and concurrency.

## Code Overview

`load.py` - This runs the ETL pipeline to convert the CSV into our structured SQLite database with the above schema. It splits up the creation of the DB schema and reading from CSV, placing them in the data/ folder.

`analysis.py` - This conducts the analytics, ingesting the data from the DB and caches the results back in for performance.

`app.py` - This takes the data transformed by `analysis.py` and generates the interactive dashboard for it.

Tasks:
> - Part 1: Accomplished in `load.py`
> - Part 2: Creates summary table with relative frequency of each cell population with the 5 desired columns of sample, total_count, population, count, and percentage.
> - Part 3: Performs statistical tests (Mann-Whitney U) to compare relative cell frequencies between responders and non-responders to determine significance, plotting it with boxplots. Filters allow for future exploration beyond listed requirement of melanoma, miraclib, and PBMC.
> - Part 4: Explores more information about the subset of the data explored (melanoma, miraclib, and PBMC), with the time_from_treatment being 0, and extra demographics about their project, sex, and response status.
> - Bonus: Calculates matching rows for the bonus question, giving the average number of B cells.
