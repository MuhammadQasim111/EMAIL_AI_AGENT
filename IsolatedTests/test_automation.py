
# agents-sdk-course-2/email-agent/magents/automation_agent.py

from agents.agent import Agent # Import your Agent class
from tools.email_tools import reply_to_email, unsubscribe_from_email, get_automated_emails
from models.email_models import EmailContext, AutomationResult # Assuming EmailContext is part of your models
from agents.runner import Runner
# Define instructions for the Automation Agent
AUTOMATION_INSTRUCTIONS = """
You are the automation agent. Your job is to:
1. Process emails marked for automated handling.
2. Decide appropriate actions:
    - Reply to the email (for simple queries that can be answered automatically)
    - Unsubscribe from mailing lists (for marketing emails, newsletters, or unwanted communications)
    - Ignore the email (for spam or low-priority automated notifications)
3. Execute the chosen action using the available tools.

You have the following tools available:
- `get_automated_emails(context: EmailContext)`: Retrieves the list of emails marked for automated processing.
- `reply_to_email(email_id: str, reply_body: str, context: EmailContext)`: Sends an automated reply to an email.
- `unsubscribe_from_email(email_id: str, context: EmailContext)`: Unsubscribes from a mailing list or newsletter.

First, get the list of emails marked for automated processing using the `get_automated_emails` tool.
Then, for each email:
1. Analyze the content.
2. Determine the most appropriate action.
3. Execute the action using the appropriate tool (`reply_to_email` or `unsubscribe_from_email`).
4. Record the result using the `record_automation_result` method of the context.

Finally, provide a summary of all actions taken.
"""

class AutomationAgent:
    def __init__(self):
        self.agent = Agent(
            name="automation_agent",
            instructions=AUTOMATION_INSTRUCTIONS,
            tools=[reply_to_email, unsubscribe_from_email, get_automated_emails],
            model="gemini-1.5-flash-latest" # Or your preferred Gemini model
        )

    async def process_automated_emails(self, context: EmailContext) -> str:
        """
        Initiates the processing of automated emails by the automation agent.
        """
        # The prompt for the LLM should guide it to use the tools
        prompt = "Begin processing emails marked for automation. Use the `get_automated_emails` tool first."

        # The Runner will handle the loop of calling the agent, executing tools, etc.
        result = await Runner.run(self.agent, [{"role": "user", "content": prompt}], context=context)
        return result.final_output

