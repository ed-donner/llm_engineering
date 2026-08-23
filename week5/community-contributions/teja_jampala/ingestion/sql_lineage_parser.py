import sqlglot
from sqlglot import exp
from retrieval.lineage_engine import LineageEngine

engine = LineageEngine()

def process_sql_file(file_path):
    with open(file_path, "r") as f:
        sql = f.read()

    try:
        lineage = engine.extract_lineage(sql)
    except Exception as e:
        print(f"❌ Lineage extraction failed: {e}")
        return [], [], None

    print("✅ Lineage extracted:", lineage)

    table = file_path.split("/")[-1].replace(".sql", "")

    records = []

    for rec in lineage:
        target = rec.get("target")
        sources = rec.get("sources", [])
        expression = rec.get("expression", "")

        doc = f"""
                Target Column: {target}
                Source Columns: {sources}
                Expression: {expression}
              """.strip()

        metadata = {
            "type": "sql",
            "table": table,
            "target": target,
            "sources": ",".join(sources)
        }

        records.append((doc, metadata))

    return records, lineage, table