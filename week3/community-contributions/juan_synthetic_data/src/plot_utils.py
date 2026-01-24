import pandas as pd

# -------------------------------
# Helper function to display CSV
# -------------------------------
def display_reference_csv(file):
    if file is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(file.name if hasattr(file, "name") else file)
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})
