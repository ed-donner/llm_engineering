"""
KUCCPS cluster constants: grades, clusters, subject name-to-code mapping.
Ported from TypeScript (GuestCalculator) — no UI.
"""
from typing import TypedDict

# KCSE grade letters and points (max 12 per subject, E = 0)
Grade = str

GRADE_POINTS: dict[Grade, int] = {
    "A": 12,
    "A-": 11,
    "B+": 10,
    "B": 9,
    "B-": 8,
    "C+": 7,
    "C": 6,
    "C-": 5,
    "D+": 4,
    "D": 3,
    "D-": 2,
    "E": 0,
}

# Subject name (as in cluster config) -> KCSE subject code
SUBJECT_NAME_TO_CODE: dict[str, str] = {
    "ENGLISH": "ENG",
    "MATHEMATICS": "MAT A",
    "KISWAHILI": "KIS",
    "PHYSICS": "PHY",
    "CHEMISTRY": "CHE",
    "BIOLOGY": "BIO",
    "GEOGRAPHY": "GEO",
    "HISTORY": "HIS",
    "CRE": "CRE",
    "BUSINESS STUDIES": "BST",
}


class ClusterConfig(TypedDict):
    id: str
    name: str
    description: str
    subjects: dict[str, int]
    examples: list[str]


# KUCCPS clusters with weighted subjects (weight 4 = primary, 2 = secondary)
KUCCPS_CLUSTERS: list[ClusterConfig] = [
    {
        "id": "1",
        "name": "Cluster 1 - Engineering & Physical Sciences",
        "description": "Engineering, Architecture, Computer Science, Physical Sciences",
        "subjects": {
            "ENGLISH": 2,
            "MATHEMATICS": 4,
            "PHYSICS": 4,
            "CHEMISTRY": 4,
        },
        "examples": ["B.Sc. Engineering", "B.Arch", "Computer Science"],
    },
    {
        "id": "2",
        "name": "Cluster 2 - Biological Sciences",
        "description": "Medicine, Pharmacy, Nursing, Agriculture, Veterinary",
        "subjects": {
            "ENGLISH": 2,
            "MATHEMATICS": 4,
            "BIOLOGY": 4,
            "CHEMISTRY": 4,
        },
        "examples": ["Medicine", "Pharmacy", "Nursing", "Agriculture"],
    },
    {
        "id": "3",
        "name": "Cluster 3 - Business & Economics",
        "description": "Commerce, Economics, Actuarial Science, Finance",
        "subjects": {
            "ENGLISH": 4,
            "MATHEMATICS": 4,
            "KISWAHILI": 2,
            "BUSINESS STUDIES": 2,
        },
        "examples": ["B.Com", "Economics", "Actuarial Science"],
    },
    {
        "id": "4A",
        "name": "Cluster 4A - Education (Science)",
        "description": "B.Ed Science - teaching Math, Physics, Chemistry, Biology",
        "subjects": {
            "ENGLISH": 2,
            "MATHEMATICS": 4,
            "PHYSICS": 2,
            "CHEMISTRY": 2,
            "BIOLOGY": 2,
        },
        "examples": ["B.Ed (Science)", "B.Ed (Mathematics)"],
    },
    {
        "id": "4B",
        "name": "Cluster 4B - Education (Arts)",
        "description": "B.Ed Arts - teaching Languages, Humanities",
        "subjects": {
            "ENGLISH": 4,
            "MATHEMATICS": 2,
            "KISWAHILI": 2,
            "GEOGRAPHY": 2,
            "HISTORY": 2,
            "CRE": 2,
        },
        "examples": ["B.Ed (Arts)", "B.Ed (Languages)"],
    },
    {
        "id": "5",
        "name": "Cluster 5 - Arts & Social Sciences",
        "description": "Law, Journalism, Social Work, Public Administration",
        "subjects": {
            "ENGLISH": 4,
            "KISWAHILI": 4,
            "GEOGRAPHY": 2,
            "HISTORY": 2,
            "CRE": 2,
        },
        "examples": ["LL.B (Law)", "Journalism", "Social Work"],
    },
]
