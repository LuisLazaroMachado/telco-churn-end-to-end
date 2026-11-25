# Telco Customer Churn: End-to-End Analysis

Predicting which telecom customers will leave, and what to do about it.
Built on the IBM Telco Customer Churn dataset (7,043 customers, 21 columns).

**Phase 1: Excel.** Power Query cleaning, pivot tables, logistic
regression trained with Solver, evaluation, business-impact analysis,
interactive dashboard and a VBA reset button.

## Dashboard

![Dashboard](docs/images/01_dashboard.png)

Interactive: slicers filter the charts and heat map, and a scroll bar moves
the decision threshold and updates precision, recall and F1.

![Fiber optic view](docs/images/02_dashboard_fiber.png)

## Key findings

| Finding | Value |
|---|---|
| Overall churn rate | 26.5% (1,869 of 7,043) |
| Month-to-month vs two-year contracts | 42.7% vs 2.8% |
| Customers in their first year (0-11 months) | 48.3% |
| Highest-risk group: new, month-to-month, fiber optic | 70.6% |

**Recommendation:** offer incentives to move month-to-month customers to
longer contracts, focusing on their first year.

## Model

Logistic regression with 5 predictors, fitted in Excel with Solver
(maximum likelihood). Evaluated on a held-out test set (20%, 1,408 customers).

| Metric (threshold 0.30) | Value |
|---|---|
| Precision | 54.5% |
| Recall | 74.1% |
| F1 | 62.8% |
| AUC | about 0.82 |

![Confusion matrix](docs/images/06_confusion_matrix.png)
![ROC curve](docs/images/05_roc_curve.png)

## How it was built

1. **Cleaning (Power Query):** typed columns, fixed 11 blank `TotalCharges`,
   created the target flag and model variables.

   ![Power Query](docs/images/03_power_query.png)

2. **Exploration:** pivot tables and charts by contract, tenure and
   contract x tenure.
3. **Model (Solver):** maximize log-likelihood on the training set.

   ![Solver](docs/images/04_solver.png)

4. **Evaluation:** confusion matrix, precision/recall/F1, ROC and AUC.
5. **Business impact:** net benefit by threshold under editable assumptions.
6. **Automation:** VBA macro that resets slicers and threshold.

## Repository structure

```
excel/    telco_churn_project.xlsx and .xlsm (with macro)
python/   notebook, churn_utils.py and tests
data/     dataset description (CSV not included, see data/README.md)
docs/     screenshots and decisions.md (assumptions and limitations)
sql/      queries (SQLite)
powerbi/  Power BI report (.pbix) and DAX measures
```

To run it: `pip install -r requirements.txt`, then `python -m pytest python/tests`.

## Requirements

Excel 2019 or later (tested in Excel 2021). Power Query, Solver and the
VBA macro are required. In the .xlsm version, enable macros when opening.

## Limitations

See [docs/decisions.md](docs/decisions.md). Business figures use invented
assumptions and are illustrative.

## Roadmap

- [x] Excel: cleaning, analysis, model, dashboard, VBA
- [x] SQL: same questions answered with queries
- [x] Python: pandas, scikit-learn, pytest
- [x] Trees and ensembles with SHAP
- [x] Power BI dashboard
- [ ] LLM-generated retention messages via API

## License

MIT

## Phase 2: Python

The same analysis repeated in Python (pandas, scikit-learn, SHAP) with the same
train/test split and features, to validate the Excel model and compare it with
tree ensembles.

| Model | AUC (test) |
|---|---|
| Logistic regression, Excel (Solver) | 0.815 |
| Logistic regression, Python | 0.818 |
| Random Forest, 5 variables | 0.830 |
| Random Forest, 45 columns | 0.838 |

Python and Excel agree. Tree ensembles gain about 0.02 AUC over the simple
regression, measured on a single train/test split.

SHAP shows what drives the Random Forest predictions. Color shows the feature
value, not risk. Contract type, tenure, fiber optic, no online security and
electronic check payment are associated with higher churn (not proven causes).

![SHAP summary](docs/images/07_shap_summary.png)

Notebook: [python/01_churn_analysis.ipynb](python/01_churn_analysis.ipynb)

## Phase 3: SQL

The same questions answered with SQL (SQLite). The CSV is loaded into a local
database and queried from `sql/`.

| Query | Result |
|---|---|
| Churn by contract (month-to-month / one year / two year) | 42.71% / 11.27% / 2.83% |
| Churn by tenure (0-11 / 60-72 months) | 48.28% / 6.68% |
| New, month-to-month, fiber optic customers | 70.55% (618 of 876) |

All figures match the Excel and Python results.

To run it: `python python/load_to_sqlite.py`, then
`python python/run_query.py sql/02_churn_by_contract.sql`.

## Phase 4: Power BI

The same dashboard rebuilt in Power BI with DAX measures: KPI cards, churn
rate by contract and by tenure group, a contract x tenure heat map and an
`InternetService` slicer.

![Power BI dashboard](docs/images/08_powerbi_dashboard.png)

Filtering by fiber optic raises the highest-risk cell (month-to-month,
0-11 months) from 51.94% to 70.55%, matching the Excel, Python and SQL results.

![Power BI, fiber optic](docs/images/09_powerbi_fiber.png)

Report file: [powerbi/telco_churn.pbix](powerbi/telco_churn.pbix) (requires
Power BI Desktop, Windows). The data is embedded, so it opens without the CSV;
Refresh will fail unless you point the source to your own copy.
DAX measures: [powerbi/measures.dax](powerbi/measures.dax).