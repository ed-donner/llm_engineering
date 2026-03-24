tools = [
    {
        "type": "function",
        "function": {
            "name": "get_all_specialties",
            "description": "Fetch all distinct specialties from the doctors table.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_specialist_info",
            "description": "Fetch all doctors available for a given specialty. Always pass the full specialty name e.g. 'Dermatology' not 'Dermatologist'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": "string",
                        "description": "The medical specialty e.g. Dermatology, Cardiology, Pediatrics, Orthopedics"
                    }
                },
                "required": ["specialty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_availability_slots",
            "description": "Fetch all availability slots for a given doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {
                        "type": "string",
                        "description": "Full name of the doctor e.g. Dr. Lim Wei"
                    }
                },
                "required": ["doctor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment for a patient with a doctor at a specific slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string"},
                    "patient_email": {"type": "string"},
                    "patient_phone": {"type": "string"},
                    "doctor_name": {"type": "string"},
                    "day_of_week": {
                        "type": "string",
                        "description": "Must match exactly e.g. 'Monday' not 'monday'"
                    },
                    "time": {
                        "type": "string",
                        "description": "Must be in HH:MM format e.g. '09:00'"
                    },
                    "reason": {"type": "string"}
                },
                "required": ["patient_name", "patient_email", "patient_phone", "doctor_name", "day_of_week", "time", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_confirmation_email",
            "description": "Send an appointment confirmation email to the patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_email": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "doctor_name": {"type": "string"},
                    "day_of_week": {"type": "string"},
                    "time": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["patient_email", "patient_name", "doctor_name", "day_of_week", "time", "reason"]
            }
        }
    }
]