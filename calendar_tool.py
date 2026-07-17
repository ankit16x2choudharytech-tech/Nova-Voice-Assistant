import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import datetime
import json
import uuid
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

MOCK_FILE = "bookings_mock.json"

def read_mock_bookings() -> list:
    """Reads mock bookings from the local JSON file."""
    if not os.path.exists(MOCK_FILE):
        return []
    try:
        with open(MOCK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading mock bookings: {e}")
        return []

def write_mock_bookings(bookings: list):
    """Writes mock bookings to the local JSON file."""
    try:
        with open(MOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(bookings, f, indent=4)
    except Exception as e:
        print(f"❌ Error writing mock bookings: {e}")

def get_calendar_service():
    """Retrieves Google Calendar service or raises exception if not authenticated."""
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json:
        try:
            info = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(info, ['https://www.googleapis.com/auth/calendar.events'])
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"❌ Failed to parse GOOGLE_TOKEN_JSON environment variable: {e}")

    if not os.path.exists('token.json'):
        raise Exception("Calendar is not authenticated. Missing token.json.")
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.events'])
    return build('calendar', 'v3', credentials=creds)

def check_availability(date_iso: str) -> str:
    """Checks Google Calendar (or local Mock fallback) for busy slots on a specific date."""
    try:
        # Cross-platform / cross-version robust ISO datetime parsing
        try:
            dt = datetime.datetime.fromisoformat(date_iso.replace('Z', '+00:00'))
        except ValueError:
            clean_str = date_iso.split('.')[0].split('+')[0].split('-')[0]
            if len(clean_str) > 10:
                dt = datetime.datetime.strptime(clean_str[:19], "%Y-%m-%dT%H:%M:%S")
            else:
                dt = datetime.datetime.strptime(clean_str[:10], "%Y-%m-%d")
        
        target_date_str = dt.strftime('%Y-%m-%d')

        if not os.path.exists('token.json'):
            print(f"⚠️ token.json missing. Using Mock Calendar Fallback to check availability on {target_date_str}.")
            bookings = read_mock_bookings()
            busy_times = []
            
            for b in bookings:
                try:
                    b_dt = datetime.datetime.fromisoformat(b['start'].replace('Z', '+00:00'))
                except ValueError:
                    clean_start = b['start'].split('.')[0].split('+')[0].split('-')[0]
                    b_dt = datetime.datetime.strptime(clean_start[:19], "%Y-%m-%dT%H:%M:%S")
                
                if b_dt.strftime('%Y-%m-%d') == target_date_str:
                    busy_times.append(f"- Blocked from {b['start']} to {b['end']} ({b['summary']})")
                    
            if not busy_times:
                return f"The calendar is completely free on {target_date_str}."
            return f"Existing events on {target_date_str}:\n" + "\n".join(busy_times)

        # Real Google Calendar logic
        service = get_calendar_service()
        start_of_day = dt.replace(hour=0, minute=0, second=0).isoformat()
        end_of_day = dt.replace(hour=23, minute=59, second=59).isoformat()
        calendar_id = os.getenv("HOST_CALENDAR_ID", "primary")
        
        events_result = service.events().list(
            calendarId=calendar_id, timeMin=start_of_day, timeMax=end_of_day, 
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            return f"The calendar is completely free on {dt.strftime('%Y-%m-%d')}."
            
        busy_times = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'Busy')
            busy_times.append(f"- Blocked from {start} to {end} ({summary})")
            
        return f"Existing events on {dt.strftime('%Y-%m-%d')}:\n" + "\n".join(busy_times)
        
    except Exception as e:
        print(f"❌ CALENDAR ERROR in check_availability: {e}")
        return f"Failed to check availability: {str(e)}"

def book_meeting(date_time_iso: str, name: str = "User") -> str:
    """Creates a 30-minute Google Calendar (or local Mock fallback) meeting."""
    try:
        # Cross-platform / cross-version robust ISO datetime parsing
        try:
            start_time = datetime.datetime.fromisoformat(date_time_iso.replace('Z', '+00:00'))
        except ValueError:
            clean_str = date_time_iso.split('.')[0].split('+')[0].split('-')[0]
            start_time = datetime.datetime.strptime(clean_str[:19], "%Y-%m-%dT%H:%M:%S")
            
        end_time = start_time + datetime.timedelta(minutes=30)

        if not os.path.exists('token.json'):
            print("⚠️ token.json missing. Using Mock Calendar Fallback to book meeting.")
            meeting_id = str(uuid.uuid4())
            new_booking = {
                "id": meeting_id,
                "guest": name,
                "summary": f"NovaVoice Demo: {name}",
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "htmlLink": "https://calendar.google.com/"
            }
            
            bookings = read_mock_bookings()
            bookings.append(new_booking)
            write_mock_bookings(bookings)
            
            print(f"✅ MOCK CALENDAR BOOKING SUCCESS (Local): {name} at {start_time.isoformat()}")
            return f"Success! Meeting booked on Google Calendar (Mock Fallback) for {name}."

        # Real Google Calendar logic
        service = get_calendar_service()
        calendar_id = os.getenv("HOST_CALENDAR_ID", "primary")

        event = {
            'summary': f'NovaVoice Demo: {name}',
            'description': 'Automated booking created via Gemini Live AI Calling Assistant.',
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': end_time.isoformat()},
        }

        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"✅ REAL CALENDAR BOOKING SUCCESS: {event_result.get('htmlLink')}")
        return f"Success! Meeting booked on Google Calendar for {name}."
        
    except Exception as e:
        print(f"❌ CALENDAR ERROR in book_meeting: {e}")
        return f"Failed to book meeting: {str(e)}"

def list_upcoming_meetings() -> list:
    """Lists upcoming bookings matching 'NovaVoice Demo:' on Google Calendar (or local Mock fallback)."""
    try:
        if not os.path.exists('token.json'):
            print("⚠️ token.json missing. Using Mock Calendar Fallback to list meetings.")
            bookings = read_mock_bookings()
            # Sort by start date
            bookings.sort(key=lambda x: x['start'])
            # Filter upcoming (from start of today)
            today_start = datetime.datetime.utcnow().date().isoformat()
            upcoming = [b for b in bookings if b['start'] >= today_start]
            return upcoming

        # Real Google Calendar logic
        service = get_calendar_service()
        calendar_id = os.getenv("HOST_CALENDAR_ID", "primary")
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        meetings = []
        for event in events:
            summary = event.get('summary', '')
            if "NovaVoice Demo" in summary:
                parts = summary.split(":", 1)
                guest = parts[1].strip() if len(parts) > 1 else "Unknown"
                
                meetings.append({
                    "id": event.get("id"),
                    "guest": guest,
                    "summary": summary,
                    "start": event['start'].get('dateTime', event['start'].get('date')),
                    "end": event['end'].get('dateTime', event['end'].get('date')),
                    "htmlLink": event.get("htmlLink")
                })
        return meetings
    except Exception as e:
        print(f"❌ CALENDAR ERROR in list_upcoming_meetings: {e}")
        return []

def find_event(guest_email: str, date_time_iso: str = None) -> dict:
    """Finds an event by guest_email and optional date_time (supports Mock fallback)."""
    try:
        target_dt = None
        if date_time_iso:
            try:
                target_dt = datetime.datetime.fromisoformat(date_time_iso.replace('Z', '+00:00'))
            except ValueError:
                clean_str = date_time_iso.split('.')[0].split('+')[0].split('-')[0]
                target_dt = datetime.datetime.strptime(clean_str[:19], "%Y-%m-%dT%H:%M:%S")

        if not os.path.exists('token.json'):
            print("⚠️ token.json missing. Using Mock Calendar Fallback to search event.")
            bookings = read_mock_bookings()
            
            for b in bookings:
                if guest_email.lower() in b['guest'].lower():
                    if target_dt:
                        try:
                            start_dt = datetime.datetime.fromisoformat(b['start'].replace('Z', '+00:00'))
                        except ValueError:
                            clean_start = b['start'].split('.')[0].split('+')[0].split('-')[0]
                            start_dt = datetime.datetime.strptime(clean_start[:19], "%Y-%m-%dT%H:%M:%S")
                        
                        if abs((start_dt - target_dt).total_seconds()) < 15 * 60:
                            return b
                    else:
                        return b
            return None

        # Real Google Calendar logic
        service = get_calendar_service()
        calendar_id = os.getenv("HOST_CALENDAR_ID", "primary")
        now = datetime.datetime.utcnow()
        time_min = (now - datetime.timedelta(days=7)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        for event in events:
            summary = event.get('summary', '')
            if "NovaVoice Demo" in summary and guest_email.lower() in summary.lower():
                if target_dt:
                    start_str = event['start'].get('dateTime', event['start'].get('date'))
                    try:
                        start_dt = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    except ValueError:
                        clean_start = start_str.split('.')[0].split('+')[0].split('-')[0]
                        start_dt = datetime.datetime.strptime(clean_start[:19], "%Y-%m-%dT%H:%M:%S")
                    
                    if abs((start_dt - target_dt).total_seconds()) < 15 * 60:
                        return event
                else:
                    return event
        return None
    except Exception as e:
        print(f"❌ Error in find_event: {e}")
        return None

def cancel_meeting(event_id: str) -> str:
    """Deletes a meeting by event ID (supports Mock fallback)."""
    try:
        if not os.path.exists('token.json'):
            print(f"⚠️ token.json missing. Using Mock Calendar Fallback to cancel event {event_id}.")
            bookings = read_mock_bookings()
            updated = [b for b in bookings if b['id'] != event_id]
            if len(updated) == len(bookings):
                return f"Could not find a mock meeting with ID {event_id}."
            write_mock_bookings(updated)
            return "Success! Meeting cancelled successfully."

        # Real Google Calendar logic
        service = get_calendar_service()
        calendar_id = os.getenv("HOST_CALENDAR_ID", "primary")
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return "Success! Meeting cancelled successfully."
    except Exception as e:
        print(f"❌ CALENDAR ERROR in cancel_meeting: {e}")
        return f"Failed to cancel meeting: {str(e)}"

def cancel_meeting_by_details(guest_email: str, date_time_iso: str) -> str:
    """Finds a meeting by guest email and time, then deletes it."""
    event = find_event(guest_email, date_time_iso)
    if not event:
        return f"Could not find a meeting for {guest_email} at {date_time_iso}."
    return cancel_meeting(event['id'])

def reschedule_meeting(event_id: str, new_date_time_iso: str) -> str:
    """Reschedules an event by Google Calendar ID to a new ISO datetime (supports Mock fallback)."""
    try:
        try:
            start_time = datetime.datetime.fromisoformat(new_date_time_iso.replace('Z', '+00:00'))
        except ValueError:
            clean_str = new_date_time_iso.split('.')[0].split('+')[0].split('-')[0]
            start_time = datetime.datetime.strptime(clean_str[:19], "%Y-%m-%dT%H:%M:%S")
            
        end_time = start_time + datetime.timedelta(minutes=30)

        if not os.path.exists('token.json'):
            print(f"⚠️ token.json missing. Using Mock Calendar Fallback to reschedule event {event_id}.")
            bookings = read_mock_bookings()
            found = False
            for b in bookings:
                if b['id'] == event_id:
                    b['start'] = start_time.isoformat()
                    b['end'] = end_time.isoformat()
                    found = True
                    break
            
            if not found:
                return f"Could not find a mock meeting with ID {event_id}."
                
            write_mock_bookings(bookings)
            return f"Success! Meeting rescheduled on Google Calendar (Mock Fallback) to {start_time.strftime('%Y-%m-%d %H:%M')}."

        # Real Google Calendar logic
        service = get_calendar_service()
        calendar_id = os.getenv("HOST_CALENDAR_ID", "primary")
        
        body = {
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': end_time.isoformat()}
        }
        
        event_result = service.events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()
        return f"Success! Meeting rescheduled on Google Calendar to {start_time.strftime('%Y-%m-%d %H:%M')}."
    except Exception as e:
        print(f"❌ CALENDAR ERROR in reschedule_meeting: {e}")
        return f"Failed to reschedule meeting: {str(e)}"

def reschedule_meeting_by_details(guest_email: str, current_date_time_iso: str, new_date_time_iso: str) -> str:
    """Finds a meeting by details, then reschedules it to a new time."""
    event = find_event(guest_email, current_date_time_iso)
    if not event:
        return f"Could not find a meeting for {guest_email} at {current_date_time_iso}."
    return reschedule_meeting(event['id'], new_date_time_iso)