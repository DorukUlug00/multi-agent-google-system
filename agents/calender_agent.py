from pydantic import BaseModel

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


class EventDateTime(BaseModel):
    dateTime: str | None = None
    timeZone: str = "Europe/Prague"

class Attendee(BaseModel):
    email: str
    name: str | None = None

class CalendarLLMOutputFormatter(BaseModel):
    action: str  # "get-next-event" or "create-event"
    # get-next-event
    time_min: str | None = None
    time_max: str | None = None
    max_results: int | None = None
    # create-event
    summary: str | None = None
    location: str | None = None
    description: str | None = None
    start: EventDateTime | None = None
    end: EventDateTime | None = None
    recurrence: list[str] | None = None
    attendees: list[Attendee] | None = None


class GoogleCalenderAgent(Agent):
    def __init__(self, role, job, output_format, response=""):
        super().__init__(role, job, output_format, response)
        self.service = create_service()


    def assign_action(self, prompt):
        final_prompt = f"""
            Role: {self.role}
            Job: Determine the action needed to complete this event
            Output: 
                {{
                    action: One value from the following list -- [get-next-event, create-event],
                    # if action == get-next-event
                    time_min: find it from context
                    time_max: find it from context
                    max_results: find it from context
                    # if action == create-event
                    summary: find it from context,
                    location: find it from context,
                    description: find it from context,
                    start: {
                        "dateTime": find it from context,
                        "timeZone": "Europe/Prague",
                    },
                    end: {
                        "dateTime": find it from context,
                        "timeZone": "Europe/Prague",
                    },
                    recurrence: [
                        find it from context
                    ],
                    attendees: [
                        {"email": find it from context, "name": find it from context},
                    ]
                }}
            User Prompt: {prompt}
        """

        self.response = client.responses.parse(
            model="gpt-4o-mini",
            input=final_prompt,
            text_format=CalendarLLMOutputFormatter
        )

        if "create-event" in self.response.output_text.lower():
            print("Will create an event")

        elif "get-next-event" in self.response.output_text.lower():
            print("Will get the next event")
            self.get_next_event(self.response.output_parsed)


    def get_next_event(self, output):
        try:
            min_time = output.time_min
            max_time = output.time_max
            max_results = output.max_results

            if not min_time or min_time is None:
                print("No min time found.")
                min_time = dt.datetime.now(dt.timezone.utc).isoformat()

            if not max_time:
                max_time = None

            if not max_results:
                max_results = 1

            print("Min time: ", min_time, "of type ", type(min_time))

            event_result = self.service.events().list(calendarId='primary', timeMin=min_time, timeMax=max_time, maxResults=max_results, singleEvents=True, orderBy='startTime').execute()
            events = event_result.get("items")

            if not events:
                print("No upcoming events found.")
                return
            else:
                print("Upcoming events found.")
                for event in events:
                    print(event)
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    print(start, event["summary"])

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
