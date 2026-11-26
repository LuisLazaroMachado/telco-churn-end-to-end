-- Relational schema for the IBM Telco dataset (PostgreSQL).
-- One row per customer is split into five related tables.
-- NULL in a service column means the service does not apply
-- (for example, online_security is NULL for customers without internet).

DROP TABLE IF EXISTS services, accounts, customers, contracts, payment_methods CASCADE;

CREATE TABLE contracts (
    contract_id   SMALLINT PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    length_months SMALLINT NOT NULL CHECK (length_months IN (1, 12, 24))
);

CREATE TABLE payment_methods (
    payment_method_id SMALLINT PRIMARY KEY,
    name              TEXT NOT NULL UNIQUE,
    is_automatic      BOOLEAN NOT NULL
);

CREATE TABLE customers (
    customer_id    TEXT PRIMARY KEY,
    gender         TEXT NOT NULL CHECK (gender IN ('Female', 'Male')),
    senior_citizen BOOLEAN NOT NULL,
    partner        BOOLEAN NOT NULL,
    dependents     BOOLEAN NOT NULL
);

CREATE TABLE accounts (
    customer_id       TEXT PRIMARY KEY REFERENCES customers (customer_id) ON DELETE CASCADE,
    tenure_months     SMALLINT NOT NULL CHECK (tenure_months >= 0),
    contract_id       SMALLINT NOT NULL REFERENCES contracts (contract_id),
    payment_method_id SMALLINT NOT NULL REFERENCES payment_methods (payment_method_id),
    paperless_billing BOOLEAN NOT NULL,
    monthly_charges   NUMERIC(8, 2) NOT NULL CHECK (monthly_charges > 0),
    total_charges     NUMERIC(10, 2) NOT NULL CHECK (total_charges >= 0),
    churned           BOOLEAN NOT NULL
);

CREATE TABLE services (
    customer_id       TEXT PRIMARY KEY REFERENCES customers (customer_id) ON DELETE CASCADE,
    phone_service     BOOLEAN NOT NULL,
    multiple_lines    BOOLEAN,
    internet_service  TEXT NOT NULL CHECK (internet_service IN ('DSL', 'Fiber optic', 'No')),
    online_security   BOOLEAN,
    online_backup     BOOLEAN,
    device_protection BOOLEAN,
    tech_support      BOOLEAN,
    streaming_tv      BOOLEAN,
    streaming_movies  BOOLEAN,
    -- internet add-ons must be NULL exactly when there is no internet service
    CHECK ((internet_service = 'No') = (online_security IS NULL)),
    CHECK (phone_service OR multiple_lines IS NULL)
);

-- Lookup values used in the dataset
INSERT INTO contracts VALUES
    (1, 'Month-to-month', 1),
    (2, 'One year', 12),
    (3, 'Two year', 24);

INSERT INTO payment_methods VALUES
    (1, 'Electronic check', FALSE),
    (2, 'Mailed check', FALSE),
    (3, 'Bank transfer (automatic)', TRUE),
    (4, 'Credit card (automatic)', TRUE);

-- Speeds up the frequent filters and joins used in the analysis queries
CREATE INDEX idx_accounts_contract ON accounts (contract_id);
CREATE INDEX idx_services_internet ON services (internet_service);
