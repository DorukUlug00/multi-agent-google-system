from agents.main_agent import Agent
from agents.client import client

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