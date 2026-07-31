from agents.main_agent import Agent
from agents.calender_agent import GoogleCalenderAgent

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

