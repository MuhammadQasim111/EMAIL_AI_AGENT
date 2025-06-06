# agents-sdk-course-2/email-agent/magents/manager_agent.py

from agents.agent import Agent # Import your Agent class
from tools.email_tools import save_emails_to_human_review, save_emails_to_automation, get_statistics
from models.email_models import EmailContext # Assuming EmailContext is part of your models
from agents.runner import Runner  # Import Runner from its module
import json
from typing import List, Dict, Any

# Define instructions for the Manager Agent
MANAGER_INSTRUCTIONS = """
You are the manager agent. Your primary job is to classify incoming emails into two categories:
1.  **Human Review:** Emails that require a human to read and respond to, or that contain sensitive information.
2.  **Automated Processing:** Emails that can be handled automatically (e.g., newsletters, marketing offers, support ticket updates).

You have the following tools available:
- `save_emails_to_human_review(email_ids: List[str], context: EmailContext)`: Marks emails for human review.
- `save_emails_to_automation(email_ids: List[str], context: EmailContext)`: Marks emails for automated processing.
- `get_statistics(context: EmailContext)`: Retrieves current email processing statistics.

For each email provided, analyze its subject and body to determine the correct category.
Prioritize human review for confidential, legal, or direct client communication.
Prioritize automation for promotional, informational, or routine updates.

After classifying all emails, summarize the actions taken.
"""

class ManagerAgent:
    def __init__(self):
        self.agent = Agent(
            name="manager_agent",
            instructions=MANAGER_INSTRUCTIONS,
            tools=[save_emails_to_human_review, save_emails_to_automation, get_statistics],
            model="gemini-1.5-flash-latest" # Or your preferred Gemini model
        )

    async def process_emails(self, emails_data: List[Dict[str, Any]], context: EmailContext) -> str:
        """
        Processes a list of email dictionaries using the manager agent.
        """
        # The prompt for the LLM should guide it to use the tools
        prompt = f"Here are emails to classify:\n{json.dumps(emails_data, indent=2)}\n\n" \
                 "Analyze each email and use the appropriate tool (`save_emails_to_human_review` or `save_emails_to_automation`) " \
                 "to categorize them. Then, provide a summary of your classifications."

        # The Runner will handle the loop of calling the agent, executing tools, etc.
        # We're passing the context so tools can interact with it.
        result = await Runner.run(self.agent, [{"role": "user", "content": prompt}], context=context)
        return result.final_output

