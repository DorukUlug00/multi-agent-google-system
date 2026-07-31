from agents.client import client

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