"""Example vulnerable code for testing security analysis."""

# Example 1: SQL Injection vulnerability
def get_user_by_id(user_id):
    import sqlite3

    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = conn.execute(query).fetchone()
    return result


# Example 2: Command Injection
def ping_host(hostname):
    import os

    command = f"ping -c 1 {hostname}"
    os.system(command)


# Example 3: Path Traversal
def read_file(filename):
    file_path = f"/var/data/{filename}"
    with open(file_path, "r") as f:
        return f.read()


# Example 4: Hardcoded credentials
def connect_to_database():
    import psycopg2

    connection = psycopg2.connect(
        host="localhost", database="mydb", user="admin", password="admin123"
    )
    return connection


# Example 5: Insecure random number generation
def generate_token():
    import random

    return "".join([str(random.randint(0, 9)) for _ in range(32)])
