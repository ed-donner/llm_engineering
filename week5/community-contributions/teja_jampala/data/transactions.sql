WITH base_txn AS (
    SELECT
        txn_id,
        acct_id,
        amount,
        txn_date,
        txn_type
    FROM stg_transactions
),

enriched_txn AS (
    SELECT
        txn_id AS transaction_id,
        acct_id AS account_id,
        amount AS transaction_amount,
        txn_date AS transaction_date,
        UPPER(txn_type) AS transaction_type
    FROM base_txn
),

account_summary AS (
    SELECT
        account_id,
        SUM(transaction_amount) AS total_amount,
        COUNT(*) AS txn_count
    FROM enriched_txn
    GROUP BY account_id
)

SELECT * FROM account_summary;