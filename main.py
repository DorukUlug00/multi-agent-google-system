from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("API_KEY"))

class Agent:
    def __init__(self, role, job, output_format, response=""):
        self.role = role
        self.job = job
        self.output_format = output_format
        self.response = response

    def act(self, user_prompt):
        final_prompt = f"""
            Role: {self.role}
            Job: {self.job}
            Output Format: {self.output_format}
            User Prompt: {user_prompt}
        """

        self.response = client.responses.create(
            model="gpt-4o-mini",
            input=final_prompt,
        )

        return self.response


class GoogleCalenderAgent(Agent):
    def __init__(self, role, job, output_format, response=""):
        super().__init__(role, job, output_format, response)

    def assign_action(self, user_prompt):
        final_prompt = f"""
            Role: {self.role}
            Job: Determine the action needed to complete this event
            Output Format: {self.output_format}
            User Prompt: {user_prompt}
        """

        self.response = client.responses.create(
            model="gpt-4o-mini",
            input=final_prompt
        )

        print(self.response.output_text.lower())

        if "schedule a meeting" in self.response.output_text.lower():
            print("Has Meeting")
            self.create_meeting()

    def create_meeting(self):
        print(f"Meeting created")


agent_role = "Chief Google Tools Manager"
agent_task = "Determine which Google Tools shall be used for helping the user"
agent_output_format = """
    tools = [] # List of strings
"""
agent = Agent(agent_role, agent_task, agent_output_format)

calender_agent = GoogleCalenderAgent("Google Calender Manager",
                                     "Managing Actions in Google Calender",
                                     "Action: String")

input_prompt = input("What can I help you with? ")

agent_response = agent.act(input_prompt)

print(agent_response.output_text)

if "Google Calendar" in agent_response.output_text:
    print("Has Google Calendar")
    calender_agent.assign_action(input_prompt)
    print(calender_agent.response.output_text)
else:
    print("Has no Google Calendar")

