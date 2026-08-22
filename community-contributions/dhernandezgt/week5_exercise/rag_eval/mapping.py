"""
Maps the short `source_doc` values used in the eval CSV (e.g. "RFC791")
to the actual corpus file paths (e.g. "txt/ipv4/RFC791_IPv4.txt").

Extend RFC_FILE_MAP as your corpus grows. If you have many files, use
`build_map_from_directory()` instead of hand-listing them.
"""
from __future__ import annotations
import os
import re
from typing import Dict, List, Optional

# Hand-curated mapping based on the corpus described.
# Add new entries here as you add RFCs to the corpus.
RFC_FILE_MAP: Dict[str, str] = {
    "RFC1034": "txt/application/RFC1034_DNS_Concepts.txt",
    "RFC1035": "txt/application/RFC1035_DNS_Implementation.txt",
    "RFC791":  "txt/ipv4/RFC791_IPv4.txt",
    "RFC792":  "txt/ipv4/RFC792_ICMP.txt",
    "RFC826":  "txt/ipv4/RFC826_ARP.txt",
    "RFC4861": "txt/ipv6/RFC4861_IPv6_Neighbor_Discovery.txt",
    "RFC2328": "txt/routing/RFC2328_OSPFv2.txt",
    "RFC2453": "txt/routing/RFC2453_RIP_v2.txt",
    "RFC4271": "txt/routing/RFC4271_BGP4.txt",
    "RFC768":  "txt/transport/RFC768_UDP.txt",
    "RFC793":  "txt/transport/RFC793_TCP.txt",
}

# Matches "RFC791", "RFC 791", "rfc-791" etc. -- space/hyphen between letters and digits is optional.
_RFC_ID_RE = re.compile(r"RFC[\s\-]?(\d+)", re.IGNORECASE)


def normalize_rfc_id(value: str) -> Optional[str]:
    """Extract a single canonical 'RFCxxxx' id from any messy string form.
    If the string contains multiple ids (e.g. 'RFC 768/RFC 793'), returns the FIRST one --
    use normalize_rfc_ids() when you need all of them (e.g. cross-document questions)."""
    if not value:
        return None
    m = _RFC_ID_RE.search(str(value))
    if not m:
        return None
    return f"RFC{m.group(1)}"


def normalize_rfc_ids(value: str) -> List[str]:
    """Extract ALL RFC ids present in a string, e.g. 'RFC 768/RFC 793' -> ['RFC768', 'RFC793'].
    Use this for source_doc values that reference more than one document (cross-doc questions)."""
    if not value:
        return []
    return [f"RFC{m}" for m in _RFC_ID_RE.findall(str(value))]


def resolve_path(source_doc: str, file_map: Dict[str, str] = None) -> Optional[str]:
    """CSV's 'RFC791' -> 'txt/ipv4/RFC791_IPv4.txt' (or None if unmapped).
    For multi-doc source_doc values, resolves only the first id -- use resolve_paths() for all."""
    file_map = file_map or RFC_FILE_MAP
    rfc_id = normalize_rfc_id(source_doc)
    if rfc_id is None:
        return None
    return file_map.get(rfc_id)


def resolve_paths(source_doc: str, file_map: Dict[str, str] = None) -> List[str]:
    """Resolves ALL RFC ids in a (possibly multi-doc) source_doc value to file paths."""
    file_map = file_map or RFC_FILE_MAP
    return [file_map[rid] for rid in normalize_rfc_ids(source_doc) if rid in file_map]


def build_map_from_directory(root_dir: str) -> Dict[str, str]:
    """
    Auto-build the mapping by walking a corpus directory and matching
    filenames like 'RFC791_IPv4.txt' -> key 'RFC791'.
    Use this instead of the hard-coded map if your corpus is large or changes often.
    """
    file_map: Dict[str, str] = {}
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            rfc_id = normalize_rfc_id(fname)
            if rfc_id:
                rel_path = os.path.relpath(os.path.join(dirpath, fname), root_dir)
                file_map[rfc_id] = rel_path
    return file_map


def source_matches(retrieved_source: str, gold_source_doc: str) -> bool:
    """
    True if a retrieved chunk's source path corresponds to ANY of the RFCs
    named in the CSV's gold `source_doc` value. Handles multi-doc values
    like 'RFC 768/RFC 793' (cross-document questions), and is robust to
    path prefixes / filename suffixes / spacing differing.
    """
    retrieved_id = normalize_rfc_id(retrieved_source)
    if retrieved_id is None:
        return False
    return retrieved_id in set(normalize_rfc_ids(gold_source_doc))
