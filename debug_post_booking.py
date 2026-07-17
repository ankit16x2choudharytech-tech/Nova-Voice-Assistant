import traceback
from api_server import app

app.testing = True
with app.test_client() as client:
    payload = {'title':'Voice Agent Booking','date_time':'2026-07-22T11:00:00+05:30','guest_email':'voice-user@example.com'}
    try:
        resp = client.post('/api/book_meeting', json=payload)
        print('STATUS', resp.status_code)
        print('DATA', resp.get_data(as_text=True))
    except Exception:
        traceback.print_exc()
