"""
Patient Knowledge Base for Call Center RAG Pipeline.
Simulates a vector database or document store of patient records.
Contains patient demographic, health insurance claims, chronic illness, hospital visits, and stays.
"""

PATIENT_DB = [
    {
        "patient_id": "P001",
        "name": "John Doe",
        "dob": "1955-04-12",
        "demographics": "69-year-old male, residing in Seattle, WA.",
        "insurance": "Medicare Part A & B, Secondary: Blue Cross Blue Shield.",
        "chronic_illnesses": ["Type 2 Diabetes", "Hypertension", "Osteoarthritis"],
        "hospital_visits": [
            {"date": "2023-01-15", "reason": "Routine checkup and blood work", "department": "Endocrinology"},
            {"date": "2023-06-22", "reason": "Knee pain consultation", "department": "Orthopedics"}
        ],
        "hospital_stays": [
            {"admitted": "2022-11-05", "discharged": "2022-11-08", "reason": "Mild heart attack observation", "ward": "Cardiology ER"}
        ],
        "claims": [
            {"date": "2023-01-15", "amount": 250.00, "status": "Paid", "description": "Consultation & Lab"},
            {"date": "2022-11-05", "amount": 12500.00, "status": "Paid", "description": "Inpatient cardiology observation"}
        ]
    },
    {
        "patient_id": "P002",
        "name": "Jane Smith",
        "dob": "1982-08-25",
        "demographics": "41-year-old female, residing in Austin, TX.",
        "insurance": "Aetna Employer Sponsored Plan.",
        "chronic_illnesses": ["Asthma"],
        "hospital_visits": [
            {"date": "2023-03-10", "reason": "Asthma flare-up", "department": "Pulmonology"},
            {"date": "2023-09-05", "reason": "Annual physical", "department": "General Practice"}
        ],
        "hospital_stays": [],
        "claims": [
            {"date": "2023-03-10", "amount": 400.00, "status": "Pending", "description": "Specialist Visit + Inhaler Prescription"}
        ]
    }
]

def retrieve_patient_records(query: str) -> str:
    """
    Mock RAG retriever.
    Searches PATIENT_DB for a match on name or ID and returns formatted text
    so the LLM can process it as 'retrieved context'.
    """
    query_lower = query.lower().strip()
    
    matched_patient = None
    for p in PATIENT_DB:
        if query_lower in p["name"].lower() or query_lower == p["patient_id"].lower():
            matched_patient = p
            break
            
    if not matched_patient:
        return f"No records found for query: '{query}'. Please verify spelling or ID."
        
    # Construct textual representation of the patient record for the LLM
    context = []
    context.append(f"Patient Name: {matched_patient['name']}")
    context.append(f"Patient ID: {matched_patient['patient_id']}")
    context.append(f"DOB: {matched_patient['dob']}")
    context.append(f"Demographics: {matched_patient['demographics']}")
    context.append(f"Insurance: {matched_patient['insurance']}")
    context.append(f"Chronic Illnesses: {', '.join(matched_patient['chronic_illnesses'])}")
    
    context.append("\nHospital Visits:")
    if not matched_patient['hospital_visits']:
        context.append("- None on record")
    else:
        for visit in matched_patient['hospital_visits']:
            context.append(f"- {visit['date']}: {visit['reason']} ({visit['department']})")
            
    context.append("\nHospital Stays:")
    if not matched_patient['hospital_stays']:
        context.append("- None on record")
    else:
        for stay in matched_patient['hospital_stays']:
            context.append(f"- Admitted: {stay['admitted']}, Discharged: {stay['discharged']}. Reason: {stay['reason']} ({stay['ward']})")
            
    context.append("\nInsurance Claims:")
    if not matched_patient['claims']:
        context.append("- None on record")
    else:
        for claim in matched_patient['claims']:
            context.append(f"- {claim['date']}: ${claim['amount']} - {claim['description']} [Status: {claim['status']}]")
            
    return "\n".join(context)
