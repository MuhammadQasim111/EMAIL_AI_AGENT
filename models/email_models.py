
# agents-sdk-course-2/email-agent/models/email_models.py

import uuid
from typing import List, Dict, Any, Optional

# Assuming pydantic is installed for data models
from pydantic import BaseModel, Field

# Define the Email model
class Email(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: str
    is_read: bool = False
    folder: str = "inbox"
    attachments: List[Any] = [] # Keeping Any for simplicity, but could be more specific

# Define a model for automation results (if your agent uses this)
class AutomationResult(BaseModel):
    action: str
    result: str
    email_id: str

class EmailContext:
    def __init__(self, initial_emails: List[Email] = None):
        self.emails: Dict[str, Email] = {email.id: email for email in (initial_emails if initial_emails else [])}
        self.human_review_ids: set[str] = set()
        self.automation_ids: set[str] = set()
        self.human_review_results: Dict[str, str] = {}
        self.automation_results: Dict[str, Dict[str, str]] = {}
        self.recipients_from_excel: List[Dict[str, str]] = [] # New: To store recipients from Excel

    def get_email_by_id(self, email_id: str) -> Optional[Email]:
        return self.emails.get(email_id)

    def save_to_human_review(self, email_ids: List[str]):
        for email_id in email_ids:
            if email_id in self.emails:
                self.human_review_ids.add(email_id)
                # logging.info(f"Email {email_id} marked for human review.") # Use Chainlit for logging in app.py

    def save_to_automation(self, email_ids: List[str]):
        for email_id in email_ids:
            if email_id in self.emails:
                self.automation_ids.add(email_id)
                # logging.info(f"Email {email_id} marked for automation.") # Use Chainlit for logging in app.py

    def get_human_review_emails(self) -> List[Email]:
        return [self.emails[e_id] for e_id in self.human_review_ids if e_id in self.emails]

    def get_automated_emails(self) -> List[Email]:
        return [self.emails[e_id] for e_id in self.automation_ids if e_id in self.emails]
    
    def record_human_review_result(self, email_id: str, summary: str):
        self.human_review_results[email_id] = summary

    def record_automation_result(self, email_id: str, action: str, result: str):
        self.automation_results[email_id] = {"action": action, "result": result}

    def get_statistics(self) -> Dict[str, int]:
        return {
            "total_emails": len(self.emails),
            "processed_emails": len(self.human_review_ids) + len(self.automation_ids),
            "human_review_count": len(self.human_review_ids),
            "automation_count": len(self.automation_ids),
        }

    def add_recipients_from_excel(self, recipients: List[Dict[str, str]]):
        """Adds recipients parsed from an Excel file."""
        self.recipients_from_excel.extend(recipients)

    def get_recipients_from_excel(self) -> List[Dict[str, str]]:
        """Returns the list of recipients from Excel."""
        return self.recipients_from_excel

