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
            Task: Read the user prompt and produce a structured Google Calendar action.
        
            Rules:
            - Choose `action`: "get-next-event" to read/list events, "create-event" to make one.
            - All datetimes must be RFC3339 with a UTC offset, e.g. 2026-08-03T09:00:00+02:00.
            - Today is {dt.datetime.now(dt.timezone.utc).isoformat()}. Resolve relative dates ("tomorrow", "next Monday") against it.
        
            For get-next-event:
            - Fill time_min/time_max only if the user gives a range; otherwise leave null.
            - Set max_results if the user asks for a count (e.g. "my next 3 events"), else null.
        
            For create-event:
            - Fill summary, location, description, start, end from the prompt.
            - If no end time is given, default end to one hour after start.
            - Use timeZone "Europe/Prague" unless the user specifies otherwise.
            - recurrence uses RRULE strings, e.g. ["RRULE:FREQ=WEEKLY;COUNT=10"]; leave null if not recurring.
            - attendees: extract any emails/names mentioned; leave null if none.
            
            For delete-event:
            - Fill time_min/time_max only if the user gives a range; otherwise leave null.
        
            Leave every field not relevant to the chosen action as null.
        
            User Prompt: {prompt}
        """

        self.response = client.responses.parse(
            model="gpt-4o-mini",
            input=final_prompt,
            text_format=CalendarLLMOutputFormatter
        )

        if "create-event" in self.response.output_text.lower():
            print("Will create an event")
            self.create_event(self.response.output_parsed)

        elif "get-next-event" in self.response.output_text.lower():
            print("Will get the next event")
            self.get_next_event(self.response.output_parsed)

        elif "delete-event" in self.response.output_text.lower():
            print("Will delete the event")
            self.delete_event(self.response.output_parsed)


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
                return None
            else:
                print("Upcoming events found.")
                if len(events) == 1:
                    event = events[0]
                    print(event)
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    print(start, event["summary"])
                    return events[0]["id"]

            for event in events:
                    print(event)
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    print(start, event["summary"])

        except HttpError as error:
            print('An error occurred: %s' % error)


    def create_event(self, output):
        try:
            event = {
                "summary": output.summary,
                "location": output.location,
                "description": output.description,
                "start": {
                    "dateTime": output.start.dateTime,
                    "timeZone": output.start.timeZone,
                },
                "end": {
                    "dateTime": output.end.dateTime,
                    "timeZone": output.end.timeZone,
                },
                "recurrence": [
                    output.recurrence
                ],
                "attendees": [
                    output.attendees
                ]
            }

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created {event.get('htmlLink')}")

        except HttpError as error:
            print('An error occurred: %s' % error)

    def delete_event(self, output):
        try:
            identifier = self.get_next_event(output)

            event = self.service.events().delete(calendarId='primary', eventId=identifier).execute()

            return event[0]["summary"]

        except HttpError as error:
            print('An error occurred: %s' % error)