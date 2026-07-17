import traceback
import calendar_tool

print('Calling list_upcoming_meetings()')
try:
    result = calendar_tool.list_upcoming_meetings()
    print('Result:', result)
except Exception as e:
    print('Exception occurred:')
    traceback.print_exc()
