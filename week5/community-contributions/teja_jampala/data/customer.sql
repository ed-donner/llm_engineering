WITH base_customer AS (
    SELECT
        cust_id,
        name,
        email,
        phone,
        dob,
        status
    FROM stg_customer
),

clean_customer AS (
    SELECT
        cust_id AS customer_id,
        INITCAP(name) AS customer_name,
        LOWER(email) AS email,
        TRIM(phone) AS phone,
        DATE(dob) AS date_of_birth,
        UPPER(status) AS customer_status
    FROM base_customer
)

SELECT * FROM clean_customer;