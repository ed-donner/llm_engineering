ALIASES = {
    # Customer
    "cust_id": "customer_id",
    "name": "customer_name",
    "email": "email",
    "phone": "phone",
    "dob": "date_of_birth",
    "status": "customer_status",

    # Accounts
    "acct_id": "account_id",
    "acct_type": "account_type",
    "balance": "balance",
    "currency": "currency",

    # Transactions
    "txn_id": "transaction_id",
    "amount": "transaction_amount",
    "txn_date": "transaction_date",
    "txn_type": "transaction_type"

}

COLUMN_ALIASES = {
    # direct renames
    "cust_id": "customer_id",
    "acct_id": "account_id",
    "txn_id": "transaction_id",
    "txn_type": "transaction_type",
}

DERIVED_COLUMNS = {
    "total_amount": "SUM(transaction_amount)",
    "txn_count": "COUNT(*)",
}

def resolve_alias(col):
    return ALIASES.get(col.lower(), col.lower())

def resolve_alias(col):
    return COLUMN_ALIASES.get(col.lower(), col.lower())

def resolve_transformation(column):
    return DERIVED_COLUMNS.get(column)