import networkx as nx


class LineageGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    # -------------------------------
    # NORMALIZATION
    # -------------------------------
    def _normalize(self, col, table=None):
        col = col.strip().lower()
        if table:
            return f"{table.lower()}.{col}"
        return col

    def _table_node(self, table):
        return f"table::{table.lower()}"

    # -------------------------------
    # SAFE ADD NODE / EDGE
    # -------------------------------
    def _add_node(self, node, **attrs):
        if not self.graph.has_node(node):
            self.graph.add_node(node, **attrs)

    def _add_edge(self, src, tgt, **attrs):
        if self.graph.has_edge(src, tgt):
            self.graph[src][tgt].update(attrs)
        else:
            self.graph.add_edge(src, tgt, **attrs)

    # -------------------------------
    # ADD SQL LINEAGE
    # -------------------------------
    def add_sql_lineage(self, lineage, table):
        table = table.lower()
        table_node = self._table_node(table)

        self._add_node(table_node, type="table")

        for rec in lineage:

            # ❌ skip invalid (*)
            if rec.get("target") == "*":
                continue

            target_col = self._normalize(rec["target"], table)

            self._add_node(target_col, type="column")
            self._add_edge(table_node, target_col, type="contains")

            for src in rec.get("sources", []):
                src = src.strip().lower()

                if not src:
                    continue

                # -------------------------------
                # HANDLE table.column
                # -------------------------------
                if "." in src:
                    src_table, col = src.split(".", 1)

                    src_node = self._normalize(col, src_table)
                    src_table_node = self._table_node(src_table)

                    self._add_node(src_table_node, type="table")
                    self._add_node(src_node, type="column")

                    self._add_edge(src_table_node, src_node, type="contains")

                    # table-level lineage
                    self._add_edge(src_table_node, table_node, type="table_lineage")

                else:
                    src_node = self._normalize(src)
                    self._add_node(src_node, type="column")

                # -------------------------------
                # COLUMN LINEAGE
                # -------------------------------
                self._add_edge(
                    src_node,
                    target_col,
                    type="column_lineage",
                    expression=rec.get("expression", "")
                )

    # -------------------------------
    # FIND MATCHING NODES (KEY FIX)
    # -------------------------------
    def _find_nodes(self, col):
        col = col.lower()
        matches = []

        for n, attrs in self.graph.nodes(data=True):

            # only consider column nodes
            if attrs.get("type") != "column":
                continue

            # exact match
            if n == col:
                matches.append(n)

            # table.column match
            elif n.endswith(f".{col}"):
                matches.append(n)

            # partial match (🔥 powerful)
            elif col in n:
                matches.append(n)

        return list(set(matches))

    # -------------------------------
    # COLUMN LINEAGE (MULTI-HOP)
    # -------------------------------
    def get_multi_hop(self, col, table=None):
        col = col.strip().lower()

        # try exact
        node = self._normalize(col, table)

        if self.graph.has_node(node):
            upstream = list(nx.ancestors(self.graph, node))
            downstream = list(nx.descendants(self.graph, node))

            return upstream, downstream

        # fallback to match search
        matches = self._find_nodes(col)

        if not matches:
            print(f"⚠️ Node '{col}' not found in graph")
            return [], []

        print(f"✅ Matches found: {matches}")

        upstream = set()
        downstream = set()

        for m in matches:
            upstream.update(nx.ancestors(self.graph, m))
            downstream.update(nx.descendants(self.graph, m))

        return list(upstream), list(downstream)

    # -------------------------------
    # TABLE LINEAGE
    # -------------------------------
    def get_table_lineage(self, table):
        node = self._table_node(table)

        if not self.graph.has_node(node):
            print(f"⚠️ Table '{table}' not found")
            return [], []

        upstream = [
            n for n in nx.ancestors(self.graph, node)
            if n.startswith("table::")
        ]

        downstream = [
            n for n in nx.descendants(self.graph, node)
            if n.startswith("table::")
        ]

        return upstream, downstream

    # -------------------------------
    # DEBUG
    # -------------------------------
    def get_all_nodes(self):
        return dict(self.graph.nodes(data=True))

    def debug(self):
        print("\n📊 Nodes:")
        for n, d in self.graph.nodes(data=True):
            print(n, d)

        print("\n🔗 Edges:")
        for u, v, d in self.graph.edges(data=True):
            print(u, "→", v, d)