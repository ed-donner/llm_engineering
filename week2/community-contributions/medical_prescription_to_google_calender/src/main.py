from ocr import *
from calendar_auth import *
from create_calender_events import *
from parsing_json import *
from preprocess import *

image_path = r"C:\Users\Legion\Desktop\projects\medical_prescription_to_google_calender\test_data\prescription_page-0001.jpg"

extracted_text = extract_text_from_image(image_path=image_path)
print(extracted_text)
cleaned_text = clean_text(extracted_text)
print(cleaned_text)
structured_data = preprocess_extracted_text(cleaned_text)
print(structured_data)
final_structured_data = process_dates(structured_data)
print(final_structured_data)
formatted_calender_events = format_calendar_events(final_structured_data)
print(formatted_calender_events)
validated_events = [validate_event(event) for event in formatted_calender_events]
for event in validated_events[:5]: 
    print(json.dumps(event, indent=2))
service = authenticate_google_calender()
gcal_events = convert_to_gcal_events(validated_events)

for event in gcal_events:
            create_event(service, event)
