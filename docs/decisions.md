# Decisions, assumptions and limitations

## Data cleaning
- 11 customers had an empty `TotalCharges`. All of them have `tenure = 0`
  (new customers with no invoice yet), so the blanks were replaced with 0.
- Churn rate is calculated as the average of a binary `ChurnFlag` column
  (1 = left, 0 = stayed). This avoids denominator errors when filtering pivot tables.

## Analysis
- Overall churn rate: 26.5% (1,869 of 7,043 customers).
- The 0% churn of two-year contracts in the first year is based on only
  59 customers and should be interpreted with caution.

## Model
- Logistic regression fitted with Excel Solver (GRG Nonlinear), maximizing
  the log-likelihood on the training set.
- 5 predictors: tenure, MonthlyCharges (both scaled to 0-1), and indicators
  for month-to-month contract, fiber optic and electronic check.
- Train/test split by row index (80/20: 5,635 / 1,408), reproducible.
- Test-set results at threshold 0.30: precision 54.5%, recall 74.1%,
  F1 62.8%, AUC about 0.82.

## Business impact (illustrative)
- Assumptions invented for this project, editable in the `Business` sheet:
  contact cost S/ 20, retention success rate 30%, annual customer value
  about S/ 882.
- Results are calculated on the test set only, not on the full customer base.
- The best threshold depends on contact cost: 0.05 at S/ 20, 0.30 at S/ 100,
  and no profitable campaign at S/ 200.

## Limitations
- Single train/test split, no cross-validation.
- Only 5 predictors, to keep the model explainable.
- AUC calculated with trapezoids over 21 thresholds (slightly underestimates).