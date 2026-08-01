from agents.main_agent import Agent
from agents.client import client

import os.path
import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_service():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    temp_service = build('calendar', 'v3', credentials=creds)
    return temp_service


class GoogleCalenderAgent(Agent):
    def __init__(self, role, job, output_format, response=""):
        super().__init__(role, job, output_format, response)
        self.service = create_service()


    def assign_action(self, prompt):
        final_prompt = f"""
            Role: {self.role}
            Job: Determine the action needed to complete this event
            Output: 
                One value from the following list -- [get-next-event, create-event]
            User Prompt: {prompt}
        """

        self.response = client.responses.create(
            model="gpt-4o-mini",
            input=final_prompt
        )

        print(self.response.output_text.lower())

        if "create-event" in self.response.output_text.lower():
            print("Will create an event")

        elif "get-next-event" in self.response.output_text.lower():
            print("Will get the next event")
            self.get_next_event()


    def get_next_event(self):
        try:
            now = dt.datetime.now().isoformat() + "Z"

            event_result = self.service.events().list(calendarId='primary', timeMin=now, maxResults=1, singleEvents=True).execute()
            event = event_result.get("items")

            if not event:
                print("No upcoming events found.")
                return
            else:
                print(event)
                start = event[0]["start"].get("date")
                print(start, event[0]["summary"])

        except HttpError as error:
            print('An error occurred: %s' % error)

    def create_event(self):
        try:
            event = {
                "summary": "Meeting with Clients",
                "location": "Singapore",
                "description": "Talking about future deals",
                "start": {
                    "dateTime": "2026-06-06T09:00:00+02:00",
                    "timeZone": "Europe/Prague",
                },
                "end": {
                    "dateTime": "2026-06-06T10:00:00+02:00",
                    "timeZone": "Europe/Prague",
                },
                "recurrence": [

                ],
                "attendees": [
                    {"email": "ulugdoruk@gmail.com", "name": "Doruk Ulug"},
                ]
            }

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created {event.get('htmlLink')}")

        except HttpError as error:
            print('An error occurred: %s' % error)
