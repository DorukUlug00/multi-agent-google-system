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


agent_role = "Chief Google Tools Manager"
agent_task = "Determine which Google Tools shall be used for helping the user"
agent_output_format = """
    tools = [] # List of strings
"""
agent = Agent(agent_role, agent_task, agent_output_format)
agent_response = agent.act(input("What can I help you with? "))
print(agent_response.output_text)