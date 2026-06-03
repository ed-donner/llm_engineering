from ingestion.synonyms import SYNONYMS

def expand_query(q):
    terms = q.lower().split()
    out = set(terms)

    for t in terms:
        if t in SYNONYMS:
            out.update(SYNONYMS[t])

    return " ".join(out)