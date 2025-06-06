import sys
import os
import chainlit as cl
from typing import List, Dict, Any, Optional
from models.email_models import EmailContext
from tools.email_tools import get_gmail_service, read_recipients_from_excel, send_gmail_message

GMAIL_SERVICE = None

@cl.on_chat_start
async def start():
    global GMAIL_SERVICE
    cl.user_session.set("email_context", EmailContext())
    cl.user_session.set("current_email_message", None)
    cl.user_session.set("recipients_list", [])

    await cl.Message(
        content="Hello! Upload an Excel file with a column named `Email` (case-insensitive)."
    ).send()

    try:
        await cl.Message(content="Authenticating with Gmail...").send()
        GMAIL_SERVICE = await cl.make_async(get_gmail_service)()
        if GMAIL_SERVICE:
            await cl.Message(content="Gmail authentication successful!").send()
        else:
            await cl.Message(content="**Gmail authentication failed.** Check your credentials.").send()
    except Exception as e:
        await cl.Message(content=f"Error during Gmail authentication: {e}").send()
        GMAIL_SERVICE = None

@cl.on_message
async def main(message: cl.Message):
    # Handle file upload
    if message.elements:
        for element in message.elements:
            if element.type == "file":
                file_path = element.path
                await cl.Message(content=f"Received file: {element.name}").send()
                recipients = await cl.make_async(read_recipients_from_excel)(file_path)
                if not recipients:
                    await cl.Message(content="No valid emails found in the Excel file.").send()
                    return
                cl.user_session.set("recipients_list", recipients)
                await cl.Message(content=f"Found {len(recipients)} recipient(s). Now, type your message in the chat.").send()
                return

    # If a message is provided and recipients are set, store the message
    recipients_list = cl.user_session.get("recipients_list", [])
    if recipients_list and not cl.user_session.get("current_email_message"):
        cl.user_session.set("current_email_message", message.content)
        await cl.Message(content="Message saved. Type `send emails` to send it to all recipients.").send()
        return

    # If user types 'send emails', send the message to all recipients
    if message.content.strip().lower() == "send emails":
        email_message = cl.user_session.get("current_email_message")
        if not GMAIL_SERVICE:
            await cl.Message(content="Gmail not authenticated. Restart the chat.").send()
            return
        if not recipients_list:
            await cl.Message(content="No recipients found. Upload an Excel file first.").send()
            return
        if not email_message:
            await cl.Message(content="No message provided. Type your message in the chat first.").send()
            return

        await cl.Message(content=f"Sending message to {len(recipients_list)} recipients...").send()
        sent_count = 0
        failed_recipients = []
        for recipient_data in recipients_list:
            recipient_email = recipient_data.get('email')
            if not recipient_email:
                failed_recipients.append(str(recipient_data))
                continue
            try:
                sent_status = await cl.make_async(send_gmail_message)(
                    GMAIL_SERVICE, 'me', recipient_email, "Important Message", email_message
                )
                if sent_status:
                    sent_count += 1
                    await cl.Message(content=f"✅ Sent to: `{recipient_email}`").send()
                else:
                    failed_recipients.append(recipient_email)
                    await cl.Message(content=f"❌ Failed to send to: `{recipient_email}`").send()
            except Exception as e:
                failed_recipients.append(recipient_email)
                await cl.Message(content=f"❌ Error sending to `{recipient_email}`: {e}").send()

        final_report = f"**Email Sending Complete!**\nSent: {sent_count}\n"
        if failed_recipients:
            final_report += "Failed:\n" + "\n".join(f"- {fail}" for fail in failed_recipients)
        await cl.Message(content=final_report).send()
        cl.user_session.set("current_email_message", None)
        cl.user_session.set("recipients_list", [])
        return

    # If none of the above, prompt user
    await cl.Message(
        content="Upload an Excel file with emails, type your message, then type `send emails`."
    ).send()


    