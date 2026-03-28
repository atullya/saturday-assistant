import os
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Scopes — what we can do with Gmail ───────────────────────
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE   = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE   = os.path.join(BASE_DIR, 'token.json')

# ── Connect to Gmail ──────────────────────────────────────────
def get_gmail_service():
    creds = None

    # load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # if no valid token, login via browser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # save token for next time
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

# ── Get inbox emails ──────────────────────────────────────────
def get_inbox(max_results=5):
    try:
        service  = get_gmail_service()
        results  = service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return []

        emails = []
        for msg in messages:
            detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {
                h['name']: h['value']
                for h in detail['payload']['headers']
            }

            emails.append({
                'id'      : msg['id'],
                'from'    : headers.get('From',    'Unknown'),
                'subject' : headers.get('Subject', 'No Subject'),
                'date'    : headers.get('Date',    'Unknown'),
                'unread'  : 'UNREAD' in detail.get('labelIds', [])
            })

        return emails

    except Exception as e:
        return [{"error": str(e)}]

# ── Get unread emails ─────────────────────────────────────────
def get_unread(max_results=5):
    try:
        service  = get_gmail_service()
        results  = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return []

        emails = []
        for msg in messages:
            detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {
                h['name']: h['value']
                for h in detail['payload']['headers']
            }

            emails.append({
                'id'      : msg['id'],
                'from'    : headers.get('From',    'Unknown'),
                'subject' : headers.get('Subject', 'No Subject'),
                'date'    : headers.get('Date',    'Unknown'),
            })

        return emails

    except Exception as e:
        return [{"error": str(e)}]

# ── Read full email body ──────────────────────────────────────
def read_email(index, max_results=5):
    try:
        service  = get_gmail_service()
        results  = service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages or index > len(messages):
            return {"error": f"Email #{index} not found"}

        msg_id = messages[index - 1]['id']
        detail = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()

        headers = {
            h['name']: h['value']
            for h in detail['payload']['headers']
        }

        # extract body
        body = extract_body(detail['payload'])

        # mark as read
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        return {
            'id'      : msg_id,
            'from'    : headers.get('From',    'Unknown'),
            'subject' : headers.get('Subject', 'No Subject'),
            'date'    : headers.get('Date',    'Unknown'),
            'body'    : body[:1500]  # limit body length
        }

    except Exception as e:
        return {"error": str(e)}

# ── Extract email body ────────────────────────────────────────
def extract_body(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
    else:
        data = payload['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    return body.strip() or "Could not extract email body."

# ── Search emails ─────────────────────────────────────────────
def search_emails(query, max_results=5):
    try:
        service  = get_gmail_service()
        results  = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return []

        emails = []
        for msg in messages:
            detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {
                h['name']: h['value']
                for h in detail['payload']['headers']
            }

            emails.append({
                'id'      : msg['id'],
                'from'    : headers.get('From',    'Unknown'),
                'subject' : headers.get('Subject', 'No Subject'),
                'date'    : headers.get('Date',    'Unknown'),
            })

        return emails

    except Exception as e:
        return [{"error": str(e)}]

# ── Send email ────────────────────────────────────────────────
def send_email(to, subject, body):
    try:
        service = get_gmail_service()

        msg            = MIMEMultipart()
        msg['To']      = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        raw     = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        message = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        return {"success": True, "id": message['id']}

    except Exception as e:
        return {"success": False, "error": str(e)}