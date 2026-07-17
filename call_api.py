import requests
import json

url = 'http://127.0.0.1:5000/api/list_meetings'
try:
    r = requests.get(url, timeout=5)
    print('STATUS:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print('RAW:', r.text)
except Exception as e:
    print('REQUEST ERROR:', e)
