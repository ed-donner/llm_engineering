import ollama
from db import get_connection
import mysql.connector

def text_to_sql(user_query):
    prompt = f"""
    Convert the following natural language query into an SQL statement for MySQL:

    Query: "{user_query}"

    Ensure the query is syntactically correct and does not contain harmful operations.
    Only return the SQL query without any explanation.
    """

    # Update the model name to 'llama3.2:latest'
    response = ollama.chat(model="llama3.2:latest", messages=[{"role": "user", "content": prompt}])
    sql_query = response['message']['content'].strip()
    return sql_query


# Uncomment this section if you wish to connect with mysql and fill out your credentials in db.py
'''def execute_sql_query(user_query):
    sql_query = text_to_sql(user_query)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
    except mysql.connector.Error as e:
        return {"error": f"MySQL Error: {e}"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()  # Ensure connection is closed even if an error occurs

    return result'''

# Example usage
if __name__ == "__main__":
    user_input = "Show me all users whose first name starts with the letter j in the first_name column."
    print(text_to_sql(user_input))
