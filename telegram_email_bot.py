from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from main_email_agent import EmailToEmailAgent
import yaml

# Load Telegram token from config.yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
TELEGRAM_TOKEN = config.get("telegram", {}).get("bot_token", "")

agent = EmailToEmailAgent(config_path="config.yaml")
agent.connect_email()

# In-memory state for pending emails per user
pending_emails = {}

async def mail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /mail recipient@example.com message")
        return
    recipient = args[0]
    subject = "Message from Telegram"
    body = " ".join(args[1:])
    pending_emails[update.effective_user.id] = (recipient, subject, body)
    await update.message.reply_text(
        f"Preview:\nTo: {recipient}\nSubject: {subject}\nBody: {body}\n\nReply /approve to send or /cancel to abort."
    )

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /schedule recipient@example.com meeting details")
        return
    recipient = args[0]
    meeting_details = " ".join(args[1:])
    # Use Gemini if enabled, else template
    email_data = {'sender': 'Telegram', 'subject': 'Meeting Request', 'body': meeting_details}
    if agent.config.get('ai', {}).get('enabled', False) and agent.gemini_model:
        body = agent.generate_gemini_reply(email_data)
    else:
        body = f"Dear Sir/Madam,\n\nI would like to schedule a meeting regarding: {meeting_details}.\nPlease let me know your availability.\n\nBest regards,\nYash"
    subject = "Meeting Request"
    pending_emails[update.effective_user.id] = (recipient, subject, body)
    await update.message.reply_text(
        f"Preview:\nTo: {recipient}\nSubject: {subject}\nBody: {body}\n\nReply /approve to send or /cancel to abort."
    )

async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = pending_emails.pop(update.effective_user.id, None)
    if data:
        recipient, subject, body = data
        success = agent.send_custom_email(recipient, subject, body)
        await update.message.reply_text("✅ Email sent!" if success else "❌ Failed to send email.")
    else:
        await update.message.reply_text("No pending email to approve.")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if pending_emails.pop(update.effective_user.id, None):
        await update.message.reply_text("Pending email cancelled.")
    else:
        await update.message.reply_text("No pending email to cancel.")

async def read_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emails = agent.read_new_emails()
    if not emails:
        await update.message.reply_text("No new emails.")
        return
    for idx, email in enumerate(emails):
        snippet = email['body'][:100].replace('\n', ' ')
        await update.message.reply_text(
            f"Email #{idx+1}\nFrom: {email['sender']}\nSubject: {email['subject']}\nSnippet: {snippet}\n\nReply with /reply {idx+1} to generate a professional reply."
        )

    # Store emails for reply reference
    context.user_data['read_emails'] = emails

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /reply <email_number>")
        return
    email_idx = int(args[0]) - 1
    emails = context.user_data.get('read_emails', [])
    if email_idx < 0 or email_idx >= len(emails):
        await update.message.reply_text("Invalid email number.")
        return
    email_data = emails[email_idx]
    # Generate reply using Gemini
    if agent.config.get('ai', {}).get('enabled', False) and agent.gemini_model:
        reply_body = agent.generate_gemini_reply(email_data)
    else:
        reply_body = agent.generate_improved_mock_reply(email_data)
    # Store pending reply for approval
    pending_emails[update.effective_user.id] = (email_data['sender'], f"Re: {email_data['subject']}", reply_body)
    await update.message.reply_text(
        f"Reply Preview:\nTo: {email_data['sender']}\nSubject: Re: {email_data['subject']}\nBody: {reply_body}\n\nReply /approve to send or /cancel to abort."
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("mail", mail_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("read", read_command))
    app.add_handler(CommandHandler("reply", reply_command))
    app.run_polling()

if __name__ == "__main__":
    main()