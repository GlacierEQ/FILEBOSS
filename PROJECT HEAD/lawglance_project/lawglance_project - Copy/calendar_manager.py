from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import json

class CalendarManager:
    def __init__(self, token_file='calendar_token.json'):
        self.token_file = token_file
        self.creds = self._load_credentials()
        self.service = build('calendar', 'v3', credentials=self.creds) if self.creds else None
        
    def _load_credentials(self):
        if os.path.exists(self.token_file):
            return Credentials.from_authorized_user_file(self.token_file)
        return None
        
    def save_credentials(self, token_info):
        with open(self.token_file, 'w') as token:
            token.write(json.dumps(token_info))
            
    def create_event(self, summary, start_time, duration=60):
        if not self.service:
            raise ValueError("Calendar not authenticated")
        event = {
            'summary': summary,
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': (start_time + timedelta(minutes=duration)).isoformat()}
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()
        
    def list_events(self, time_min=None, max_results=10):
        if not self.service:
            raise ValueError("Calendar not authenticated")
        time_min = time_min or datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
