
# agents-sdk-course-2/email-agent/magents/human_review_agent.py

from agents.agent import Agent # Import your Agent class
from models.email_models import EmailContext # Assuming EmailContext is part of your models
from typing import List, Dict, Any
from agents.runner import Runner
import json

# Define instructions for the Human Review Agent
HUMAN_REVIEW_INSTRUCTIONS = """
You are the human review agent. Your job is to summarize emails that require human attention.
You should analyze the content of each email marked for human review and provide a concise summary,
highlighting key information, urgent actions, or sensitive details that a human needs to know.

You have no specific tools for this task, your output is a summary.
"""

class HumanReviewAgent:
    def __init__(self):
        self.agent = Agent(
            name="human_review_agent",
            instructions=HUMAN_REVIEW_INSTRUCTIONS,
            tools=[], # This agent primarily generates text summaries, not calls external tools
            model="gemini-1.5-flash-latest" # Or your preferred Gemini model
        )

    async def summarize_emails_for_review(self, emails_data: List[Dict[str, Any]], context: EmailContext) -> str:
        """
        Summarizes emails marked for human review using the human review agent.
        """
        # The prompt for the LLM to summarize
        prompt = f"Summarize the following emails for human review, highlighting key information and urgent actions:\n{json.dumps(emails_data, indent=2)}"

        # The Runner will handle the LLM call and return the summary
        result = await Runner.run(self.agent, [{"role": "user", "content": prompt}], context=context)
        
        # After getting the summary, you might want to store it in the context
        # For this example, we'll just return the summary.
        # You could parse result.final_output and call context.record_human_review_result for each email.
        
        return result.final_output

