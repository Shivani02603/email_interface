# Open Claw Email Agent with Telegram & LLM Integration

This project is an AI-powered email agent that connects your Gmail account to a Telegram bot, allowing you to read, reply, and send emails directly from Telegram. It uses Google Gemini (LLM) to generate professional replies and supports approval workflows for outgoing emails.

## Features
- **Read Emails**: Use `/read` in Telegram to view new emails.
- **Reply with AI**: After reading, use `/reply <email_number>` to generate a professional reply using Gemini LLM, preview it, and approve before sending.
- **Send Emails**: Use `/mail recipient@example.com message` to compose and send emails from Telegram, with approval before sending.
- **Approval Workflow**: All outgoing emails require explicit approval (`/approve` or `/cancel`).
- **Modular Design**: Easily extend or integrate with other systems (like Open Claw).

## Setup
1. **Clone the repository**
   ```sh
   git clone https://github.com/Shivani02603/email_interface.git
   cd email_interface
   ```
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure your credentials**
   - Edit `config.yaml` with your Gmail, app password, and Gemini API key.
4. **Run the Telegram bot**
   ```sh
   py -3 telegram_email_bot.py
   ```

## Usage
- `/read` — List new emails. Each email can be replied to with `/reply <number>`.
- `/reply <number>` — Generate and preview a professional reply using LLM, then approve to send.
- `/mail recipient@example.com message` — Compose a new email, preview, and approve to send.
- `/approve` — Send the pending email.
- `/cancel` — Cancel the pending email.

## Requirements
- Python 3.10+
- Gmail account with App Password
- Telegram Bot Token
- Google Gemini API key (for LLM features)

## License
MIT License

---
For more details, see the code and comments. Contributions welcome!
