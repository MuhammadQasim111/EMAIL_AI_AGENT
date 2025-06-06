import streamlit as st
import os
from typing import List, Dict, Any, Optional

# Assuming 'models' and 'tools' directories are in the same parent directory as app.py
# You might need to adjust sys.path if your project structure is different
import sys
sys.path.append(os.path.dirname(__file__))

from models.email_models import EmailContext
from tools.email_tools import get_gmail_service, read_recipients_from_excel, send_gmail_message

# Global variable for Gmail service (can be managed better with st.session_state for persistence)
# However, for initial setup, we'll keep it simple and re-authenticate if necessary.
GMAIL_SERVICE = None

def authenticate_gmail():
    """Authenticates with Gmail and stores the service object."""
    global GMAIL_SERVICE
    try:
        # Streamlit doesn't have a direct equivalent of Chainlit's async make_async
        # We assume get_gmail_service is blocking or handles its own async context.
        # For a real deployment, consider how credentials will be handled securely.
        st.info("Authenticating with Gmail...")
        service = get_gmail_service()
        if service:
            GMAIL_SERVICE = service
            st.success("Gmail authentication successful!")
            return True
        else:
            st.error("**Gmail authentication failed.** Check your credentials.")
            return False
    except Exception as e:
        st.error(f"Error during Gmail authentication: {e}")
        return False

def main():
    st.set_page_config(page_title="Streamlit Email Sender", layout="centered")
    st.title("📧 Streamlit Email Sender")

    # Initialize session state variables
    if "email_context" not in st.session_state:
        st.session_state.email_context = EmailContext()
    if "current_email_message" not in st.session_state:
        st.session_state.current_email_message = ""
    if "recipients_list" not in st.session_state:
        st.session_state.recipients_list = []
    if "gmail_service" not in st.session_state:
        st.session_state.gmail_service = None

    # --- Gmail Authentication ---
    if st.session_state.gmail_service is None:
        st.write("Before proceeding, let's authenticate with Gmail.")
        if st.button("Authenticate Gmail"):
            if authenticate_gmail():
                st.session_state.gmail_service = GMAIL_SERVICE
            else:
                st.warning("Gmail authentication failed. Please try again.")

    # Only show the rest of the app if Gmail is authenticated
    if st.session_state.gmail_service:
        st.success("Gmail is authenticated!")
        st.info("Upload an Excel file with a column named `Email` (case-insensitive).")

        # --- File Uploader ---
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
        if uploaded_file is not None:
            # Save the uploaded file temporarily to read it
            file_path = os.path.join("./temp", uploaded_file.name)
            os.makedirs("./temp", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.write(f"Received file: {uploaded_file.name}")
            recipients = read_recipients_from_excel(file_path)

            if not recipients:
                st.warning("No valid emails found in the Excel file.")
                st.session_state.recipients_list = []
            else:
                st.session_state.recipients_list = recipients
                st.success(f"Found {len(recipients)} recipient(s).")
                st.write("Recipients loaded:")
                for i, r in enumerate(recipients[:5]): # Displaying first 5 recipients
                    st.write(f"- {r.get('email', 'N/A')}")
                if len(recipients) > 5:
                    st.write(f"... and {len(recipients) - 5} more.")

            # Clean up the temporary file
            os.remove(file_path)

        # --- Email Message Input ---
        st.write("---")
        st.subheader("Compose Your Email")
        current_message_input = st.text_area(
            "Your Email Message",
            value=st.session_state.current_email_message,
            height=200,
            key="email_message_input"
        )
        if current_message_input:
            st.session_state.current_email_message = current_message_input
            st.info("Message saved. Click 'Send Emails' when ready.")

        # --- Send Emails Button ---
        if st.button("Send Emails"):
            if not st.session_state.gmail_service:
                st.error("Gmail not authenticated. Please authenticate first.")
                return
            if not st.session_state.recipients_list:
                st.warning("No recipients found. Please upload an Excel file first.")
                return
            if not st.session_state.current_email_message:
                st.warning("No message provided. Please type your message in the text area.")
                return

            st.write(f"Sending message to {len(st.session_state.recipients_list)} recipients...")
            sent_count = 0
            failed_recipients = []
            progress_bar = st.progress(0)

            for i, recipient_data in enumerate(st.session_state.recipients_list):
                recipient_email = recipient_data.get('email')
                if not recipient_email:
                    failed_recipients.append(str(recipient_data))
                    continue

                try:
                    # send_gmail_message is assumed to be blocking, if it's async
                    # you'll need to wrap it with asyncio.run() or similar in a non-async context
                    sent_status = send_gmail_message(
                        st.session_state.gmail_service, 'me', recipient_email, "Important Message", st.session_state.current_email_message
                    )
                    if sent_status:
                        sent_count += 1
                        st.success(f"✅ Sent to: `{recipient_email}`")
                    else:
                        failed_recipients.append(recipient_email)
                        st.error(f"❌ Failed to send to: `{recipient_email}`")
                except Exception as e:
                    failed_recipients.append(recipient_email)
                    st.error(f"❌ Error sending to `{recipient_email}`: {e}")

                progress_bar.progress((i + 1) / len(st.session_state.recipients_list))

            st.write("---")
            final_report = f"**Email Sending Complete!**\nSent: {sent_count}\n"
            if failed_recipients:
                final_report += "Failed:\n" + "\n".join(f"- {fail}" for fail in failed_recipients)
            st.markdown(final_report)

            # Reset state after sending
            st.session_state.current_email_message = ""
            st.session_state.recipients_list = []
            st.experimental_rerun() # Rerun to clear inputs and reset the app

if __name__ == "__main__":
    main()
