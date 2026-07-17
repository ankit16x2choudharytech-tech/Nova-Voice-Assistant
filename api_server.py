import sys
import traceback
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
import traceback
from flask_cors import CORS
from calendar_tool import (
    book_meeting, 
    check_availability,
    list_upcoming_meetings,
    cancel_meeting,
    cancel_meeting_by_details,
    reschedule_meeting,
    reschedule_meeting_by_details
)

app = Flask(__name__)
CORS(app)

@app.route('/api/list_meetings', methods=['GET'])
def handle_list_meetings():
    print(f"\n📋 [API REQUEST] Listing upcoming meetings")
    meetings = list_upcoming_meetings()
    print(f"✅ [API RESPONSE] Found {len(meetings)} meetings")
    return jsonify({"meetings": meetings})


@app.route('/api/health', methods=['GET'])
def handle_health():
    return jsonify({"status": "ok"})

@app.route('/api/book_meeting', methods=['POST'])
def handle_booking():
    data = request.json
    print(f"\n🔔 [API REQUEST] Booking {data.get('title')} at {data.get('date_time')}")
    result = book_meeting(date_time_iso=data.get('date_time'), name=data.get('guest_email'))
    print(f"✅ [API RESPONSE] {result}")

    # After booking (mock or real), return the current meetings list so the UI
    # can immediately refresh the dashboard without waiting for a separate fetch.
    try:
        meetings = list_upcoming_meetings()
    except Exception as e:
        print(f"⚠️ Could not fetch meetings after booking: {e}")
        meetings = []

    return jsonify({"result": result, "meetings": meetings})

@app.route('/api/check_availability', methods=['POST'])
def handle_availability():
    data = request.json
    print(f"\n📅 [API REQUEST] Checking availability for {data.get('date')}")
    result = check_availability(date_iso=data.get('date'))
    print(f"✅ [API RESPONSE] {result}")
    return jsonify({"result": result})

@app.route('/api/cancel_meeting', methods=['POST'])
def handle_cancel():
    data = request.json
    event_id = data.get('event_id')
    guest_email = data.get('guest_email')
    date_time = data.get('date_time')
    
    if event_id:
        print(f"\n❌ [API REQUEST] Cancelling meeting with ID {event_id}")
        result = cancel_meeting(event_id)
    elif guest_email and date_time:
        print(f"\n❌ [API REQUEST] Cancelling meeting for {guest_email} at {date_time}")
        result = cancel_meeting_by_details(guest_email, date_time)
    else:
        result = "Error: Missing event ID or guest details for cancellation."
        
    print(f"✅ [API RESPONSE] {result}")
    return jsonify({"result": result})

@app.route('/api/reschedule_meeting', methods=['POST'])
def handle_reschedule():
    data = request.json
    event_id = data.get('event_id')
    guest_email = data.get('guest_email')
    current_date_time = data.get('current_date_time')
    new_date_time = data.get('new_date_time')
    
    if event_id and new_date_time:
        print(f"\n🔄 [API REQUEST] Rescheduling meeting with ID {event_id} to {new_date_time}")
        result = reschedule_meeting(event_id, new_date_time)
    elif guest_email and current_date_time and new_date_time:
        print(f"\n🔄 [API REQUEST] Rescheduling meeting for {guest_email} from {current_date_time} to {new_date_time}")
        result = reschedule_meeting_by_details(guest_email, current_date_time, new_date_time)
    else:
        result = "Error: Missing event details or new date-time for rescheduling."
        
    print(f"✅ [API RESPONSE] {result}")
    return jsonify({"result": result})

if __name__ == '__main__':
    print("🚀 Local API Bridge running on http://0.0.0.0:5000")
    # Enable debug and propagate exceptions in development to get full tracebacks
    app.debug = True
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # Add a global exception handler to ensure errors are logged to console
    @app.errorhandler(Exception)
    def handle_exception(e):
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    app.run(host='0.0.0.0', port=5000)