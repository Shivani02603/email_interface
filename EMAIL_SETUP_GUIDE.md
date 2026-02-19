# 🤖 Email to Email AI Agent

Automatically monitors your Gmail inbox and sends intelligent auto-replies using AI.

## ✨ Features

- 📧 **IMAP/SMTP Gmail Integration** - No API keys needed!
- 🤖 **AI-Powered Replies** - Context-aware auto-responses
- 🔒 **App Password Security** - Uses Gmail App Passwords (secure)
- ⚡ **Real-time Monitoring** - Checks for new emails every 30 seconds
- 📝 **Smart Context Detection** - Different replies for meetings, urgent emails, questions
- 🛡️ **Safe & Reliable** - No third-party API dependencies

## 🚀 Quick Start

### 1. Set Up Gmail App Password

1. Go to [Google Account Settings](https://myaccount.google.com/security)
2. Enable **2-Factor Authentication** (required)
3. Go to **App Passwords** section
4. Generate new App Password for "Mail"
5. Copy the 16-character password (like: `abcd efgh ijkl mnop`)

### 2. Configure the Agent

1. **Run the agent** (it will create `config.yaml`):
   ```
   start_email_agent.bat
   ```

2. **Edit `config.yaml`** with your details:
   ```yaml
   email:
     email: "your-email@gmail.com"
     app_password: "your-16-character-app-password"
   ```

3. **Restart the agent**:
   ```
   start_email_agent.bat
   ```

## ⚙️ Configuration Options

Edit `config.yaml` to customize:

```yaml
agent:
  auto_reply: true          # Enable/disable auto-replies
  reply_delay: 5           # Wait before sending (seconds)
  check_interval: 30       # Check emails every 30 seconds
  max_emails_per_check: 5  # Process max 5 emails per check

ai:
  enabled: false          # Set true for OpenAI integration
  model: "mock"           # Currently using smart mock responses
  tone: "professional"    # Response tone
```

## 🧠 AI Response Types

The agent automatically detects email context and replies appropriately:

- **📅 Meetings**: "I'll review my calendar and get back to you..."
- **🚨 Urgent**: "I've received your urgent message and will prioritize..."  
- **❓ Questions**: "Thank you for your question. I'll provide a comprehensive response..."
- **📧 General**: "Thank you for your email. I'll review it carefully..."

## 📁 Project Structure

```
open_claw_project/
├── main.py                 # Main email agent
├── config.yaml            # Your email settings
├── start_email_agent.bat  # Windows launcher
├── requirements.txt       # Python dependencies
└── logs/                  # Agent logs
    └── email_agent.log
```

## 🛠️ Troubleshooting

### "Login failed"
- Verify your Gmail App Password (16 characters, no spaces)
- Ensure 2-Factor Authentication is enabled
- Check email address spelling

### "No module named yaml"
- Run: `py -3 -m pip install PyYAML`
- Or use `start_email_agent.bat` (auto-installs)

### Agent not responding to emails
- Check `logs/email_agent.log` for errors
- Verify `auto_reply: true` in config.yaml
- Check Gmail inbox for new unread emails

## 🔄 Usage

1. **Start monitoring**: Run `start_email_agent.bat`
2. **Send test email**: Email yourself to test auto-reply
3. **Check logs**: View `logs/email_agent.log` for activity
4. **Stop agent**: Press `Ctrl+C` in the console

## 🆕 Adding OpenAI Integration

To use real AI instead of mock responses:

1. Get OpenAI API key from [OpenAI Platform](https://platform.openai.com)
2. Add to `config.yaml`:
   ```yaml
   ai:
     enabled: true
     api_key: "your-openai-api-key"
     model: "gpt-3.5-turbo"
   ```
3. Install OpenAI: `py -3 -m pip install openai`

## 📞 Support

- View logs: `logs/email_agent.log`
- Test configuration: Edit `config.yaml` and restart
- Gmail setup help: [Google App Passwords Guide](https://support.google.com/accounts/answer/185833)