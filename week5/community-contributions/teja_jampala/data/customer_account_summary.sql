SELECT
    c.customer_id,
    c.customer_name,
    a.account_id,
    a.account_type,
    a.balance,
    t.total_amount,
    t.txn_count
FROM customer_dim c
JOIN account_dim a
    ON c.customer_id = a.customer_id
JOIN (
    SELECT
        account_id,
        SUM(amount) AS total_amount,
        COUNT(*) AS txn_count
    FROM stg_transactions
    GROUP BY account_id
) t
    ON a.account_id = t.account_id;