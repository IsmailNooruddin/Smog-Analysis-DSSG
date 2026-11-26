In real-world social impact settings, data is rarely static. Environmental conditions evolve, new temporal waves of survey records are released, and administrative programs expand into adjacent geographic districts.

In Milestone 05, we will execute the Data Extension Plan originally proposed in Milestone 01. You will integrate a second data source or collection wave, conduct statistical distribution tests (covariate shift and concept drift), re-train your machine learning pipelines, and evaluate whether model performance, stability, and fairness hold up under real-world data expansion.

Required Technical & Analytical Deliverables

1. **New Data Ingestion, Cleaning & Schema Integration**

- **Data Extension Execution:** Ingest your planned second data source or collection wave (e.g., additional temporal records, new geographic regions, or external socio-demographic features).
- **Schema Reconciliation & Quality Audit:** Align feature definitions, handle missingness in newly added attributes, resolve data type discrepancies, and document the final expanded observation count (Ntotal = Ninitial + Nnew) and feature space (Ptotal).
- **Data Ingestion Pipeline:** This is very important, you should automate all merging and reconciliation steps cleanly within your code notebook.

3. **Statistical Data Drift & Concept Drift Analysis**

- **Covariate Shift / Feature Drift Testing:** Perform statistical distribution tests (e.g., two-sample Kolmogorov-Smirnov test, Chi-Square test, or Population Stability Index [PSI]) comparing feature distributions in the initial dataset against the new data wave.
- **Concept Drift Evaluation:** Assess whether the relationship between predictors (X) and the target outcome (Y) has shifted across data collection waves or regions.
- **Visualizing Distribution Shifts:** Include overlaid density plots or bar charts highlighting key features that experienced significant distribution drift.

5. **Model Re-training & Out-of-Sample Generalization**

- **Zero-Shot / Out-of-Sample Testing:** Evaluate your Milestone 04 model on the new data wave _without re-training_ to measure baseline generalization decay.
- **Model Re-training Framework:** Re-train both baseline and advanced models on the combined augmented dataset using your stratified K-Fold Cross-Validation pipeline.
- **Comparative Performance Audit:** Construct a 3-way comparison table tracking performance metrics (Accuracy, Precision, Recall, F1-Score, ROC-AUC) across three settings:

1. Initial Model evaluated on Initial Data
2. Initial Model evaluated on New Data Wave (Zero-Shot)
3. Re-trained Model evaluated on Combined Dataset

4. **Fairness Shift, Written Manuscript Update & Code Quality**

- **Algorithmic Fairness Shift:** Re-evaluate group fairness metrics (Demographic Parity, Equalized Odds, Disparate Impact Ratio) on the expanded dataset. Report whether data expansion reduced or exacerbated demographic disparities.
- **FATEN Governance Update:** Re-evaluate your system against the FATEN framework (Fairness, Autonomy, Trust, Equity, Non-maleficence) and update your real-world living lab deployment recommendations.

Evaluation Breakdown (100 Marks Total)

|   |   |   |
|---|---|---|
|**Evaluation Criterion**|**Score**|**Detailed Performance Expectations**|
|**Data Ingestion & Schema Integration**|**20 Marks**|Automated ingestion of new data wave, schema reconciliation, and clear reporting of final expanded dataset dimensions.|
|**Statistical Drift & Concept Shift Analysis**|**30 Marks**|Rigorous statistical testing (e.g., KS-test, PSI) and visual diagnostic analysis comparing feature/target distribution shifts.|
|**Model Re-training & Generalization Testing**|**30 Marks**|Zero-shot evaluation on new wave followed by systematic re-training. Clear 3-way comparative performance audit table.|
|**Fairness Shift, Manuscirpt & Code Quality**|**20 Marks**|Quantitative evaluation of fairness metric shifts post-retraining, updated FATEN policy recommendations, executable code notebook, and PDF manuscript.|

**Recommended Manuscript Design:** 

A structured 6–8 page academic manuscript formatted according to standard IEEE or Springer conference guidelines, integrating your cumulative work across the semester:

- **Title, Authors & Abstract:** Concise summary of the social problem, dataset curation, modeling methodology, key findings, and policy implications.
- **Section I: Introduction & Problem Framing:** Social context, UN Sustainable Development Goal (SDG) alignment, and research hypotheses.
- **Section II: Data Curation & Master Dataset Inventory:** Source origins, scraping/merging pipeline, preprocessing choices, and feature definitions.
- **Section III: Exploratory Data Analysis & Driver Analysis:** Univariate/bivariate visualizations, correlation insights, and feature importance drivers.
- **Section IV: Predictive Modeling & Architecture Evaluation:** Baseline models vs. advanced/ensemble architectures, cross-validation setup, and asymmetric error cost analysis.
- **Section V: Algorithmic Bias, Fairness & Ethics Audit:** Group fairness metrics (Demographic Parity, Equalized Odds), bias mitigation implementation, and Pareto trade-off curves.
- **Section VI: Data Expansion, Drift & Model Re-training:** Statistical drift testing, zero-shot generalization decay, and re-trained performance comparisons.
- **Section VII: Policy Recommendations:** FATEN governance compliance, operational failure modes, and actionable recommendations for stakeholders.