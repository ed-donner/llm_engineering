import sqlite3

DB_NAME = "support.db"

def query_db(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.commit()
    conn.close()

    return results


def lookup_user_account(email):

    result = query_db(
        "SELECT email, plan, status, balance FROM users WHERE email=?",
        (email,)
    )

    if not result:
        return "User not found"

    email, plan, status, balance = result[0]

    return {
        "email": email,
        "plan": plan,
        "status": status,
        "balance_cents": balance
    }


def issue_refund(order_id):

    order = query_db(
        "SELECT id, status FROM orders WHERE id=?",
        (order_id,)
    )

    if not order:
        return "Order not found"

    query_db(
        "UPDATE orders SET status='refund_initiated' WHERE id=?",
        (order_id,)
    )

    return {
        "order_id": order_id,
        "status": "refund initiated"
    }


def create_support_ticket(issue):

    query_db(
        "INSERT INTO tickets (issue,status) VALUES (?,?)",
        (issue, "open")
    )

    ticket = query_db(
        "SELECT id FROM tickets ORDER BY id DESC LIMIT 1"
    )

    return {
        "ticket_id": ticket[0][0],
        "status": "created"
    }