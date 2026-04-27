import sqlglot
from sqlglot import exp
from collections import defaultdict


class LineageEngine:

    def __init__(self):
        self.cte_map = {}
        self.alias_map = {}

    # -------------------------------
    # MAIN ENTRY
    # -------------------------------
    def extract_lineage(self, sql: str):
        try:
            tree = sqlglot.parse_one(sql)
        except Exception as e:
            print(f"❌ SQL parse error: {e}")
            return []

        self.cte_map = {}
        self.alias_map = {}

        # Collect CTEs first
        self._collect_ctes(tree)

        lineage = []

        # Handle WITH queries
        if isinstance(tree, exp.With):
            for select in tree.find_all(exp.Select):
                lineage.extend(self._process_select(select))
        else:
            for select in tree.find_all(exp.Select):
                lineage.extend(self._process_select(select))

        return lineage

    # -------------------------------
    # CTE HANDLING
    # -------------------------------
    def _collect_ctes(self, tree):
        for cte in tree.find_all(exp.CTE):
            self.cte_map[cte.alias] = cte.this

    # -------------------------------
    # SELECT PROCESSING
    # -------------------------------
    def _process_select(self, select):
        lineage = []

        self._build_alias_map(select)

        for proj in select.expressions:

            # Skip star early
            if isinstance(proj, exp.Star):
                continue

            if isinstance(proj, exp.Alias):
                target = proj.alias
                expr = proj.this
            else:
                target = proj.name
                expr = proj

            sources = self._extract_sources(expr)

            # Resolve CTE references
            sources = self._resolve_cte_sources(sources)

            if not target:
                continue

            lineage.append({
                "target": target,
                "sources": sources,
                "expression": proj.sql()
            })

        return lineage

    # -------------------------------
    # ALIAS MAP
    # -------------------------------
    def _build_alias_map(self, select):
        self.alias_map = {}

        for table in select.find_all(exp.Table):
            alias = table.alias_or_name
            self.alias_map[alias] = table.name

    # -------------------------------
    # SOURCE EXTRACTION
    # -------------------------------
    def _extract_sources(self, expression):
        sources = set()

        for col in expression.find_all(exp.Column):
            table = col.table
            column = col.name

            if table and table in self.alias_map:
                sources.add(f"{self.alias_map[table]}.{column}")
            elif table:
                sources.add(f"{table}.{column}")
            else:
                sources.add(column)

        return list(sources)

    # -------------------------------
    # CTE RESOLUTION
    # -------------------------------
    def _resolve_cte_sources(self, sources):
        resolved = []

        for src in sources:
            if "." in src:
                table, col = src.split(".", 1)

                if table in self.cte_map:
                    sub_tree = self.cte_map[table]
                    sub_lineage = self._process_select(sub_tree)

                    for rec in sub_lineage:
                        if rec["target"] == col:
                            resolved.extend(rec["sources"])
                else:
                    resolved.append(src)
            else:
                resolved.append(src)

        return list(set(resolved))

    # -------------------------------
    # AGGREGATION HANDLING
    # -------------------------------
    def _handle_aggregation(self, expr):
        if isinstance(expr, exp.Anonymous):
            func = expr.name.upper()

            if func in ["SUM", "COUNT", "AVG", "MIN", "MAX"]:
                return {
                    "type": "aggregation",
                    "function": func,
                    "sources": self._extract_sources(expr)
                }

        return None