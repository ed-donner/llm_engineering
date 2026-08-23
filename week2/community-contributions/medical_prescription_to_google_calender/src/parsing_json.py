import json
import re
from datetime import datetime, timedelta

# Default number of days to schedule indefinitely recurring events (1 year)
DEFAULT_DURATION_DAYS = 365  

# Function to assign a default time for general terms like "before breakfast", etc.
def assign_time(timing):
    time_mappings = {
        "random": "09:00 AM",
        "daily": "09:00 AM",
        "before breakfast": "07:00 AM",
        "after breakfast": "08:30 AM",
        "before lunch": "12:00 PM",
        "after lunch": "01:30 PM",
        "before dinner": "07:00 PM",
        "after dinner": "08:30 PM",
    }
    return time_mappings.get(timing.lower(), timing)

# Function to extract the recurrence pattern
def get_recurrence_interval(timing):
    """ Extracts interval days from 'every X days', 'once a week', or 'once a month'. """
    timing = timing.lower().strip()

    if "every alternate day" in timing:
        return 2  # Every other day (every 2 days)
    elif match := re.search(r"every (\d+) days", timing):
        return int(match.group(1))  # Extract number of days
    elif "once a week" in timing:
        return 7  # Every 7 days (once a week)
    elif "once a month" in timing:
        return "monthly"  # Special case for monthly scheduling
    elif timing in ["daily", "every day"]:
        return 1  # Every day
    else:
        return None  # Not a recurring event

# Function to convert AM/PM time format to 24-hour format
def convert_to_24hr(time_str):
    return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")

# Function to generate Google Calendar events
def format_calendar_events(processed_data):
    events = []
    start_date = datetime.today().date()

    # Medicines
    if "medicines" in processed_data:
        for med in processed_data["medicines"]:
            if med.get("name"):
                event_time = assign_time(med.get("timing", "09:00 AM"))
                interval_days = get_recurrence_interval(med["timing"])
                
                # If no interval, assume daily (default behavior)
                if interval_days is None:
                    interval_days = 1  

                # Generate events for 1 year if no duration is given
                event_date = start_date
                for _ in range(365 if interval_days != "monthly" else 12):  
                    if interval_days == "monthly":
                        event_date = (event_date.replace(day=1) + timedelta(days=32)).replace(day=1)  # Jump to the next month
                    else:
                        event_date += timedelta(days=interval_days)
                    
                    event = {
                        "summary": f"Take {med['name']} ({med.get('dosage', 'Dosage not specified')})",
                        "start": {
                            "dateTime": f"{event_date.isoformat()}T{convert_to_24hr(event_time)}:00",
                            "timeZone": "Asia/Kolkata"
                        },
                        "end": {
                            "dateTime": f"{event_date.isoformat()}T{convert_to_24hr(event_time)}:59",
                            "timeZone": "Asia/Kolkata"
                        }
                    }
                    events.append(event)

    # Tests
    if "tests" in processed_data:
        for test in processed_data["tests"]:
            if test.get("name") and test.get("dueDate"):  # Use 'dueDate' instead of 'date'
                event = {
                    "summary": f"Medical Test: {test['name']}",
                    "start": {"date": test["dueDate"]},  # Fix here
                    "end": {"date": test["dueDate"]},  # Fix here
                    "timeZone": "Asia/Kolkata"
                }
                events.append(event)


    # Follow-ups
    if "follow_ups" in processed_data:
        for follow_up in processed_data["follow_ups"]:
            if follow_up.get("date"):
                event = {
                    "summary": "Doctor Follow-up Appointment",
                    "start": {"date": follow_up["date"]},
                    "end": {"date": follow_up["date"]},
                    "timeZone": "Asia/Kolkata"
                }
                events.append(event)

    return events

# Function to validate events before sending to Google Calendar
def validate_event(event):
    required_fields = {
        "summary": "Untitled Event",
        "start": {"dateTime": datetime.today().isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": (datetime.today() + timedelta(minutes=30)).isoformat(), "timeZone": "Asia/Kolkata"}
    }

    for field, default_value in required_fields.items():
        if field not in event or event[field] is None:
            event[field] = default_value

    return event
