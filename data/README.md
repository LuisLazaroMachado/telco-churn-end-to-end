# Data

## Source
IBM Telco Customer Churn sample dataset, published on Kaggle:
https://www.kaggle.com/datasets/blastchar/telco-customer-churn

IBM also published a newer version:
https://community.ibm.com/community/user/businessanalytics/blogs/steven-macko/2019/07/11/telco-customer-churn-1113

- File: `WA_Fn-UseC_-Telco-Customer-Churn.csv`
- 7,043 rows (customers) and 21 columns
- Target variable: `Churn` (Yes/No, customers who left within the last month)

## Contents
- Services signed up for: phone, multiple lines, internet, online security,
  online backup, device protection, tech support, streaming TV and movies
- Account information: tenure, contract, payment method, paperless billing,
  monthly and total charges
- Demographics: gender, senior citizen, partner, dependents

## How to use it
The CSV is **not included** in this repository. Download it from the link
above and place it in `data/raw/`. The folder is listed in `.gitignore`
so the file is never committed by accident.

Check the license terms on the Kaggle page before redistributing the data.