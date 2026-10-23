# ----------------------------
# Database Required Utilities 
# ----------------------------

import sqlite3
import pandas as pd
from helpers.system_settings import get_system_settings


def csv_to_sqlite(
    csv_path: str, 
    db_path: str, 
    table_name: str ="products", 
    if_exists: str = "replace"
) -> int:
    """Converting a csv data format to a SQLite schema"""
    
    if if_exists not in {"fail", "replace", "append"}:
        raise ValueError("if_exists must be 'fail', 'replace', or 'append'")

    dataframe = pd.read_csv(csv_path)
    connection = sqlite3.connect(db_path)

    try:
        dataframe.to_sql(table_name, connection, if_exists=if_exists, index=False)
    finally:
        connection.close()

    return len(dataframe)



def execute_sql_query(sql_query: str):
    """Executes the given SQL Query"""
    system_settings = get_system_settings()
    print(f'- Running the given SQL Query: {sql_query}')

    with sqlite3.connect(system_settings.DB_PATH) as connection:
        cursor = connection.cursor()

        try:
            cursor.execute(sql_query)
            rows = cursor.fetchall() if cursor.description is not None else []
            connection.commit()
            return rows
        
        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            cursor.close()



