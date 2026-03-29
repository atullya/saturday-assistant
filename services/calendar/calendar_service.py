import os
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow 
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _find_file(filename):
    paths = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, '..', 'gmail', filename),
        os.path.join(BASE_DIR, '..', '..', filename),
        os.path.join(os.getcwd(), filename),
    ]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            return p
    return os.path.abspath(os.path.join(BASE_DIR, filename))

TOKEN_FILE = _find_file('token.json')

def _find_credentials():
    paths = [
        os.path.join(BASE_DIR, 'credentials.json'),
        os.path.join(BASE_DIR, '..', 'gmail', 'credentials.json'),
        os.path.join(BASE_DIR, '..', '..', 'credentials.json'),
        os.path.join(os.getcwd(), 'credentials.json'),
    ]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            return p
    return None

def get_calendar_service():
    creds      = None
    creds_file = _find_credentials()

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # ← this part was missing — opens browser for login
            if not creds_file:
                raise FileNotFoundError("credentials.json not found!")
            flow  = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # save new token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def get_upcoming_events(max_results=5):
    try:
        service = get_calendar_service()
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return result.get('items', [])
    except Exception as e:
        return {"error": str(e)}

def get_today_events():
    try:
        service = get_calendar_service()
        now   = datetime.datetime.utcnow()
        start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0).isoformat() + 'Z'
        end   = datetime.datetime(now.year, now.month, now.day, 23, 59, 59).isoformat() + 'Z'
        result = service.events().list(
            calendarId='primary',
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return result.get('items', [])
    except Exception as e:
        return {"error": str(e)}

def add_event(title, date_str, time_str=None, duration_minutes=60, description=""):
    try:
        service = get_calendar_service()
        today   = datetime.date.today()

        if date_str.lower() == "today":
            date = today
        elif date_str.lower() == "tomorrow":
            date = today + datetime.timedelta(days=1)
        else:
            # try multiple formats
            for fmt in ("%Y-%m-%d", "%b %d", "%B %d", "%d-%m-%Y"):
                try:
                    parsed = datetime.datetime.strptime(date_str, fmt)
                    # if no year in format, use current year
                    date = parsed.replace(year=today.year).date()
                    break
                except ValueError:
                    continue
            else:
                return {"error": f"Could not parse date '{date_str}'. Use: today / tomorrow / YYYY-MM-DD / Mar 30"}

        # rest of function stays same...
        if time_str:
            # handle both "10:00" and "10:00 AM/PM"
            for tfmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
                try:
                    parsed_time = datetime.datetime.strptime(time_str, tfmt).time()
                    break
                except ValueError:
                    continue
            else:
                return {"error": f"Could not parse time '{time_str}'. Use: 14:30 or 2:30 PM"}

            dt_start = datetime.datetime.combine(date, parsed_time)
            dt_end   = dt_start + datetime.timedelta(minutes=duration_minutes)
            event = {
                'summary'    : title,
                'description': description,
                'start'      : {'dateTime': dt_start.isoformat(), 'timeZone': 'Asia/Kathmandu'},
                'end'        : {'dateTime': dt_end.isoformat(),   'timeZone': 'Asia/Kathmandu'},
            }
        else:
            event = {
                'summary'    : title,
                'description': description,
                'start'      : {'date': date.isoformat()},
                'end'        : {'date': (date + datetime.timedelta(days=1)).isoformat()},
            }

        return service.events().insert(calendarId='primary', body=event).execute()
    except Exception as e:
        return {"error": str(e)}

def delete_event(event_id):
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"success": True, "message": "Event deleted."}
    except Exception as e:
        return {"error": str(e)}

def format_events(events):
    if not events:
        return "📭 No events found!"
    if isinstance(events, dict) and "error" in events:
        return f"❌ {events['error']}"
    lines = []
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date', ''))
        if 'T' in start:
            dt       = datetime.datetime.fromisoformat(start)
            time_str = dt.strftime("%b %d, %I:%M %p")
        else:
            dt       = datetime.datetime.strptime(start, "%Y-%m-%d")
            time_str = dt.strftime("%b %d (all day)")
        lines.append(f"📅 **{e['summary']}** — {time_str}\n      ID: `{e['id']}`")
    return "\n".join(lines)