"""
KUCCPS cluster points calculation.
Formula: C = sqrt((r/R) × (t/T)) × 48
- r = raw cluster (sum of best 4 cluster subject points)
- R = 48 (max raw cluster)
- t = aggregate (sum of best 7 subject points)
- T = 84 (max aggregate)
"""
from __future__ import annotations

from typing import Any

from .constants import (
    GRADE_POINTS,
    KUCCPS_CLUSTERS,
    SUBJECT_NAME_TO_CODE,
    ClusterConfig,
    Grade,
)


def get_cluster_by_id(cluster_id: str) -> ClusterConfig | None:
    """Return cluster config by id (e.g. '1', '2', '4A')."""
    for c in KUCCPS_CLUSTERS:
        if c["id"] == cluster_id:
            return c
    return None


def _get_subject_code(cluster_subject_name: str) -> str:
    return SUBJECT_NAME_TO_CODE.get(
        cluster_subject_name.upper(), cluster_subject_name
    )


def calculate_aggregate(subject_grades: dict[str, Grade]) -> tuple[int, list[dict[str, Any]]]:
    """
    Compute KCSE aggregate from best 7 subjects (grade > E).
    subject_grades: map of subject code -> grade (e.g. {"ENG": "A", "MAT A": "B+"}).
    Returns (aggregate, best7_list).
    """
    points_list = []
    for code, grade in subject_grades.items():
        if not grade or grade == "E":
            continue
        pts = GRADE_POINTS.get(grade, 0)
        points_list.append({"code": code, "grade": grade, "points": pts})
    points_list.sort(key=lambda x: x["points"], reverse=True)
    best7 = points_list[:7]
    aggregate = sum(s["points"] for s in best7)
    return aggregate, best7


def calculate_cluster_points(
    cluster_id: str,
    subject_grades: dict[str, Grade],
) -> dict[str, Any]:
    """
    Compute raw cluster, weighted cluster, and breakdown for the given cluster.
    subject_grades: map of subject code -> grade (e.g. {"ENG": "A", "MAT A": "B+"}).
    Uses KUCCPS formula: C = sqrt((r/48) * (t/84)) * 48.
    """
    cluster = get_cluster_by_id(cluster_id)
    if not cluster:
        return {
            "error": f"Unknown cluster id: {cluster_id}",
            "weighted": 0.0,
            "raw_cluster": 0,
            "aggregate": 0,
            "cluster_subjects": [],
            "best7": [],
        }

    aggregate, best7 = calculate_aggregate(subject_grades)

    # Cluster subjects: for each (name, weight) get code, grade, points
    cluster_subjects = []
    for subject_name, weight in cluster["subjects"].items():
        code = _get_subject_code(subject_name)
        grade = subject_grades.get(code, "E")
        points = GRADE_POINTS.get(grade, 0)
        cluster_subjects.append({
            "subject": code,
            "name": subject_name,
            "grade": grade,
            "points": points,
            "weight": weight,
        })

    # Sort by weighted contribution (points * weight), take best 4
    sorted_cluster = sorted(
        cluster_subjects,
        key=lambda s: s["points"] * s["weight"],
        reverse=True,
    )[:4]
    raw_cluster = sum(s["points"] for s in sorted_cluster)

    # KUCCPS formula
    r, R = raw_cluster, 48
    t, T = aggregate, 84
    if R > 0 and T > 0:
        weighted = (r / R * t / T) ** 0.5 * 48
    else:
        weighted = 0.0
    weighted = round(weighted, 3)

    return {
        "cluster_id": cluster_id,
        "cluster_name": cluster["name"],
        "weighted": weighted,
        "raw_cluster": raw_cluster,
        "aggregate": aggregate,
        "cluster_subjects": sorted_cluster,
        "best7": best7,
    }
