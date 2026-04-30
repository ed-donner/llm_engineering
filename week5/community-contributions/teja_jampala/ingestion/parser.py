import os
import pandas as pd


def clean(val):
    if pd.isna(val):
        return ""
    return str(val).strip()


def parse_files(folder):
    records = []

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if file.endswith(".sql"):
            continue

        try:
            if file.endswith(".csv"):
                df = pd.read_csv(path)
            elif file.endswith((".xls", ".xlsx")):
                df = pd.read_excel(path)
            else:
                continue
        except Exception as e:
            print(f"❌ Failed to read {file}: {e}")
            continue

        # 🔥 FIXED COLUMN NORMALIZATION
        df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

        print("📂 Processing file:", file)

        for _, row in df.iterrows():

            gold_table = clean(row.get("gold_table"))
            gold_column = clean(row.get("gold_column"))
            source_table = clean(row.get("source_table"))
            source_column = clean(row.get("source_column"))
            transformation = clean(row.get("transformation"))

            # skip invalid rows
            if not gold_table or not gold_column:
                continue

            doc = f"""
                    Gold Table: {gold_table}
                    Gold Column: {gold_column}
                    Source Table: {source_table}
                    Source Column: {source_column}
                    Transformation: {transformation}
                  """.strip()

            metadata = {
                "type": "mapping",
                "gold_table": gold_table,
                "gold_column": gold_column,
                "source_table": source_table,
                "source_column": source_column
            }

            records.append((doc, metadata))

    print(f"✅ Total mapping records: {len(records)}")

    return records