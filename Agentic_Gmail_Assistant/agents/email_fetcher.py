from googleapiclient.discovery import build
from config.config import get_credentials
from agents.classifier import ClassifierAgent

def get_unread_emails():
    """Fetches unread emails from Gmail."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])

    if not messages:
        return "No new unread emails."

    emails = []
    for msg in messages:
        msg_id = msg['id']
        msg_data = service.users().messages().get(userId='me', id=msg_id).execute()
        payload = msg_data.get('payload', {})
        headers = payload.get("headers", [])

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
        snippet = msg_data.get("snippet", "No preview available")

        emails.append({
            "id": msg_id,
            "subject": subject,
            "sender": sender,
            "preview": snippet
        })

    return emails

def rank_emails(emails):
    """Sorts emails based on priority: Urgent > Work-Related > General."""
    classifier = ClassifierAgent()
    priority_order = {"Urgent": 1, "Work-Related": 2, "General": 3}

    for email in emails:
        email['category'] = classifier.categorize_email(email['subject'], email['preview'])
        email['priority'] = priority_order[email['category']]

    return sorted(emails, key=lambda x: x['priority'])
