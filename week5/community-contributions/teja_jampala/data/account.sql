WITH base_accounts AS (
    SELECT
        acct_id,
        cust_id,
        acct_type,
        balance,
        currency
    FROM stg_accounts
),

clean_accounts AS (
    SELECT
        acct_id AS account_id,
        cust_id AS customer_id,
        UPPER(acct_type) AS account_type,
        ROUND(balance, 2) AS balance,
        UPPER(currency) AS currency
    FROM base_accounts
)

SELECT * FROM clean_accounts;