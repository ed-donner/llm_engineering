from googleapiclient.discovery import build
from calendar_auth import authenticate_google_calender 
from parsing_json import format_calendar_events  
from datetime import datetime, timedelta

def create_event(service, event_details):
    """Creates an event in Google Calendar."""
    try:
        event = service.events().insert(calendarId='primary', body=event_details).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating event: {str(e)}")

def convert_time_to_24hr(time_str):
    """Converts time from '10:30 am' format to '10:30:00'"""
    if time_str and time_str.lower() != 'none':
        try:
            parsed_time = datetime.strptime(time_str, '%I:%M %p')
            return parsed_time.strftime('%H:%M:%S')
        except ValueError:
            return '09:00:00'  
    return '09:00:00'  

def convert_to_gcal_events(formatted_events):
    """Converts formatted events into Google Calendar's format."""
    gcal_events = []
    
    for event in formatted_events:
        gcal_event = {
            'summary': event['summary'],
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': 10}]
            }
        }
        
        # Check if it's an all-day event (has 'date') or timed event (has 'dateTime')
        if 'date' in event['start']:
            # All-day event (like tests and follow-ups)
            gcal_event['start'] = {
                'date': event['start']['date'],
                'timeZone': 'Asia/Kolkata'
            }
            gcal_event['end'] = {
                'date': event['end']['date'],
                'timeZone': 'Asia/Kolkata'
            }
        else:
            # Timed event (like medicine schedules)
            start_dt = datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S')
            end_dt = start_dt + timedelta(minutes=30)
            
            gcal_event['start'] = {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Asia/Kolkata'
            }
            gcal_event['end'] = {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Asia/Kolkata'
            }
        
        gcal_events.append(gcal_event)
    
    return gcal_events
