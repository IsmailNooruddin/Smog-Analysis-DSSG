# Milestone 2 submission: Role 2 files

Trans-Boundary Smog Prediction: Crop Fires and Climate Traps across Punjab (Pakistan and India).
Munir Tariq (10067), Ismail Nooruddin (09958), Bilal Ayub (09716).

| File | What it is |
|---|---|
| `Milestone2_Report.docx` | The report (manuscript Sections I–VI: project alignment, data and preprocessing, EDA, hypotheses, limitations, reproducibility). Export it to PDF for the hand-in. |
| `merge_analysis.ipynb` | Role 2 notebook: merge of the three streams into the master table (Part 2A), the merged-data analysis (Part 2B), the hypotheses, the final checks and, in its last cell, the Excel export. Executed top to bottom; all outputs are saved in it. |
| `Milestone2_Final_Master_and_EDA.xlsx` | Written by the last cell of `merge_analysis.ipynb`. The first sheet, `Master_Daily_Final`, is the final master table (5,665 city-days × 287 columns). The `Contents` sheet lists every other sheet, the notebook that made it and the report table or figure that uses it. |

The zip also holds the three Role 1 notebooks: `air_quality.ipynb` (Person A), `weather.ipynb` (Person B) and `fire.ipynb` (Person C).

**Run order** (Kernel, Restart and Run All, from the repository root): `air_quality.ipynb`, `weather.ipynb`, `fire.ipynb`, then `merge_analysis.ipynb`.
To rerun them, the notebooks need the project repository: the helper modules in `src/` and the data in `Dataset/`.
Every notebook keeps its printed outputs and figures, so all results can be read without rerunning.
