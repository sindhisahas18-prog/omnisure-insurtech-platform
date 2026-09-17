"""
Seed configuration for the reusable claim engine — one entry per
insurance type. This is the data the product spec asked for: adding
a new insurance category's claim behavior means adding a dict here,
not writing new claim-handling code.

Each dynamic question:
  key         - stored under Claim.answers[key]
  label       - shown to the customer
  type        - "text" | "textarea" | "number" | "date" | "select"
  options     - required when type == "select"
  applies_to  - list of damaged_components this question is shown for,
                or [] to mean "always shown regardless of component"
"""

BASE_REQUIRED_DOCUMENTS = ["Identity Proof", "Policy Copy", "Incident Photos"]

BASE_QUESTIONS = [
    {"key": "incident_location", "label": "Where did this happen?", "type": "text", "applies_to": []},
    {"key": "incident_description", "label": "Describe what happened", "type": "textarea", "applies_to": []},
    {"key": "police_report_filed", "label": "Was a police/authority report filed?", "type": "select",
     "options": ["Yes", "No"], "applies_to": []},
]

CLAIM_CONFIG_SEED = {
    "car": {
        "incident_types": ["Accident", "Theft", "Fire", "Natural Calamity", "Vandalism"],
        "damaged_components": ["Bumper", "Headlight", "Door", "Bonnet", "Windshield", "Engine", "Tyre", "Mirror", "Sensors"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["RC Copy", "Driving License", "Repair Estimate"],
        "dynamic_questions": BASE_QUESTIONS + [
            {"key": "driver_at_time", "label": "Who was driving at the time?", "type": "text", "applies_to": []},
            {"key": "windshield_replace_or_repair", "label": "Does the windshield need full replacement or repair?",
             "type": "select", "options": ["Replacement", "Repair"], "applies_to": ["Windshield"]},
            {"key": "engine_water_ingress", "label": "Was there water ingress into the engine?", "type": "select",
             "options": ["Yes", "No"], "applies_to": ["Engine"]},
        ],
    },
    "bike": {
        "incident_types": ["Accident", "Theft", "Fire", "Natural Calamity"],
        "damaged_components": ["Fairing", "Headlight", "Fuel Tank", "Handlebar", "Engine", "Tyre", "Brake", "Exhaust"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["RC Copy", "Driving License", "Repair Estimate"],
        "dynamic_questions": BASE_QUESTIONS + [
            {"key": "fuel_leak", "label": "Is there a fuel leak from the tank?", "type": "select",
             "options": ["Yes", "No"], "applies_to": ["Fuel Tank"]},
        ],
    },
    "mobile": {
        "incident_types": ["Accidental Damage", "Liquid Damage", "Theft", "Screen Damage"],
        "damaged_components": ["Screen", "Camera", "Battery", "Back Glass", "Motherboard", "Charging Port"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Purchase Invoice", "IMEI Proof"],
        "dynamic_questions": BASE_QUESTIONS + [
            {"key": "device_powers_on", "label": "Does the device power on?", "type": "select",
             "options": ["Yes", "No"], "applies_to": []},
            {"key": "liquid_exposure", "label": "Was the device exposed to liquid?", "type": "select",
             "options": ["Yes", "No"], "applies_to": ["Motherboard", "Battery", "Charging Port"]},
        ],
    },
    "laptop": {
        "incident_types": ["Accidental Damage", "Liquid Damage", "Theft"],
        "damaged_components": ["Screen", "Keyboard", "Battery", "Motherboard", "Trackpad", "Charger"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Purchase Invoice", "Serial Number Proof"],
        "dynamic_questions": BASE_QUESTIONS + [
            {"key": "device_powers_on", "label": "Does the device power on?", "type": "select",
             "options": ["Yes", "No"], "applies_to": []},
        ],
    },
    "electronics": {
        "incident_types": ["Accidental Damage", "Liquid Damage", "Theft", "Power Surge"],
        "damaged_components": ["Screen", "Circuit Board", "Power Supply", "Casing", "Accessories"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Purchase Invoice"],
        "dynamic_questions": BASE_QUESTIONS,
    },
    "home": {
        "incident_types": ["Fire", "Theft", "Flood", "Storm Damage", "Structural Damage"],
        "damaged_components": ["Roof", "Door", "Furniture", "Appliance", "Electrical", "Plumbing"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Property Ownership Proof", "Repair Estimate"],
        "dynamic_questions": BASE_QUESTIONS + [
            {"key": "property_habitable", "label": "Is the property currently habitable?", "type": "select",
             "options": ["Yes", "No"], "applies_to": []},
        ],
    },
    "travel": {
        "incident_types": ["Flight Delay", "Cancellation", "Lost Baggage", "Damaged Baggage", "Medical Emergency"],
        "damaged_components": ["Flight Delay", "Cancellation", "Lost Baggage", "Damaged Baggage", "Medical Emergency"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Boarding Pass", "Airline Delay/Loss Certificate"],
        "dynamic_questions": [
            {"key": "delay_duration_hours", "label": "How many hours was the delay/how long were you affected?",
             "type": "number", "applies_to": ["Flight Delay"]},
            {"key": "baggage_tag_number", "label": "Baggage tag number", "type": "text",
             "applies_to": ["Lost Baggage", "Damaged Baggage"]},
            {"key": "medical_facility_name", "label": "Name of medical facility visited", "type": "text",
             "applies_to": ["Medical Emergency"]},
            {"key": "incident_description", "label": "Describe what happened", "type": "textarea", "applies_to": []},
        ],
    },
    "crop": {
        "incident_types": ["Crop Loss", "Rainfall Trigger", "Drought", "Flood", "Pest Damage"],
        "damaged_components": ["Crop Loss", "Rainfall Trigger", "Drought", "Flood", "Pest Damage"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Land Ownership/Lease Proof", "Crop Sowing Certificate"],
        "dynamic_questions": [
            {"key": "affected_area_acres", "label": "Affected area (in acres)", "type": "number", "applies_to": []},
            {"key": "crop_type", "label": "Crop type", "type": "text", "applies_to": []},
            {"key": "incident_description", "label": "Describe what happened", "type": "textarea", "applies_to": []},
        ],
    },
    "business": {
        "incident_types": ["Property Damage", "Equipment Damage", "Business Interruption", "Liability"],
        "damaged_components": ["Property Damage", "Equipment Damage", "Business Interruption", "Liability"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Business Registration Proof", "Financial Loss Statement"],
        "dynamic_questions": BASE_QUESTIONS + [
            {"key": "estimated_downtime_days", "label": "Estimated business downtime (days)", "type": "number",
             "applies_to": ["Business Interruption"]},
        ],
    },
    "life": {
        "incident_types": ["Death Claim"],
        "damaged_components": ["Death Claim"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Death Certificate", "Nominee ID Proof", "Medical Cause of Death Certificate"],
        "dynamic_questions": [
            {"key": "date_of_death", "label": "Date of death", "type": "date", "applies_to": []},
            {"key": "cause_of_death", "label": "Cause of death", "type": "text", "applies_to": []},
            {"key": "nominee_relationship", "label": "Nominee's relationship to the insured", "type": "text", "applies_to": []},
        ],
    },
    "livestock": {
        "incident_types": ["Animal Death", "Disease", "Accident"],
        "damaged_components": ["Animal Death", "Disease", "Accident"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Veterinary Documents", "Animal Ear-Tag/ID Proof"],
        "dynamic_questions": [
            {"key": "animal_id_tag", "label": "Animal ID / ear-tag number", "type": "text", "applies_to": []},
            {"key": "vet_name", "label": "Attending veterinarian's name", "type": "text", "applies_to": []},
            {"key": "incident_description", "label": "Describe what happened", "type": "textarea", "applies_to": []},
        ],
    },
    "health": {
        "incident_types": ["Hospitalization", "Surgery", "ICU", "Medicine", "Diagnostics", "Room Charges"],
        "damaged_components": ["Hospitalization", "Surgery", "ICU", "Medicine", "Diagnostics", "Room Charges"],
        "required_documents": BASE_REQUIRED_DOCUMENTS + ["Hospital Bills", "Discharge Summary", "Doctor's Prescription"],
        "dynamic_questions": [
            {"key": "hospital_name", "label": "Hospital name", "type": "text", "applies_to": []},
            {"key": "admission_date", "label": "Admission date", "type": "date", "applies_to": []},
            {"key": "diagnosis", "label": "Diagnosis", "type": "text", "applies_to": []},
            {"key": "cashless_or_reimbursement", "label": "Cashless or reimbursement?", "type": "select",
             "options": ["Cashless", "Reimbursement"], "applies_to": []},
        ],
    },
}
