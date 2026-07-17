import traceback
import api_server

app = api_server.app
app.testing = True

with app.test_client() as client:
    try:
        resp = client.get('/api/list_meetings')
        print('STATUS:', resp.status_code)
        print('DATA:', resp.get_data(as_text=True))
    except Exception as e:
        print('EXCEPTION:')
        traceback.print_exc()
