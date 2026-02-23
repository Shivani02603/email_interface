#!/usr/bin/env python3
"""
Email to Email AI Agent
Monitors Gmail inbox and auto-replies with AI-generated responses
Uses IMAP/SMTP with Gmail App Passwords (no API keys needed)
"""

import os
import yaml
import logging
import smtplib
import imaplib
import email
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

# Google Gemini import - handle gracefully if not installed
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Generative AI not installed. Install with: pip install google-generativeai")

class EmailToEmailAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Email to Email AI Agent"""
        self.config = self.load_config(config_path)
        self.imap_conn = None
        self.smtp_conn = None
        self.setup_logging()
        self.processed_emails = set()  # Track processed emails
        self.gemini_model = None
        self.setup_gemini()
        
    def setup_logging(self):
        """Setup logging"""
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'email_agent.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file {config_path} not found")
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required config
            required = ['email', 'app_password']
            email_config = config.get('email', {})
            
            missing = [key for key in required if not email_config.get(key)]
            if missing:
                raise ValueError(f"Missing required config: {missing}")
            
            return config
            
        except FileNotFoundError as e:
            print(f"❌ {e}")
            print("📝 Creating sample config.yaml...")
            self.create_sample_config(config_path)
            raise
        except yaml.YAMLError as e:
            print(f"❌ Error parsing YAML config: {e}")
            raise
            
    def create_sample_config(self, config_path: str):
        """Create a sample configuration file"""
        sample_config = {
            'email': {
                'email': 'your-email@gmail.com',
                'app_password': 'your-16-character-app-password',
                'imap_server': 'imap.gmail.com',
                'smtp_server': 'smtp.gmail.com',
                'imap_port': 993,
                'smtp_port': 587
            },
            'agent': {
                'auto_reply': True,
                'reply_delay': 5,
                'check_interval': 30,
                'max_emails_per_check': 5
            },
            'ai': {
                'enabled': False,
                'model': 'gemini-1.5-flash',  # Google Gemini model
                'tone': 'professional',
                'api_key': 'your-gemini-api-key-here'  # Add your Gemini API key
            }
        }
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(sample_config, f, default_flow_style=False, indent=2)
            print(f"✅ Sample config created: {config_path}")
            print("📋 Please update with your Gmail credentials")
        except Exception as e:
            print(f"❌ Failed to create sample config: {e}")
    
    def setup_gemini(self):
        """Setup Google Gemini client"""
        if not GEMINI_AVAILABLE:
            self.logger.info("Google Generative AI library not available - using mock responses")
            return False
            
        ai_config = self.config.get('ai', {})
        api_key = ai_config.get('api_key')
        
        if not api_key or api_key == 'your-gemini-api-key-here':
            self.logger.info("No Gemini API key configured - using mock responses")
            return False
        
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            # Test the model
            test_response = self.gemini_model.generate_content("Test message")
            self.logger.info("Google Gemini (gemini-2.5-flash) initialized successfully")
            return True
        except Exception as e:
            # Don't log the actual error to prevent API key leaks
            self.logger.error("Failed to setup Gemini - check API key configuration")
            return False
    
    def connect_email(self) -> bool:
        """Connect to Gmail using IMAP and SMTP"""
        email_config = self.config['email']
        
        try:
            # Connect to IMAP
            self.logger.info("Connecting to Gmail IMAP...")
            self.imap_conn = imaplib.IMAP4_SSL(email_config['imap_server'], email_config['imap_port'])
            self.imap_conn.login(email_config['email'], email_config['app_password'])
            
            # Connect to SMTP 
            self.logger.info("Connecting to Gmail SMTP...")
            self.smtp_conn = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            self.smtp_conn.starttls()
            self.smtp_conn.login(email_config['email'], email_config['app_password'])
            
            self.logger.info("Email connections established")
            return True
            
        except Exception as e:
            self.logger.error(f"Email connection failed: {e}")
            return False
    
    def read_new_emails(self) -> List[Dict[str, Any]]:
        """Read new unread emails"""
        if not self.imap_conn:
            return []
        
        try:
            self.imap_conn.select('inbox')
            status, messages = self.imap_conn.search(None, 'UNSEEN')
            
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()
            new_emails = []
            
            max_emails = self.config.get('agent', {}).get('max_emails_per_check', 5)
            
            for email_id in email_ids[-max_emails:]:  # Get latest emails
                if email_id.decode() in self.processed_emails:
                    continue
                    
                try:
                    status, msg_data = self.imap_conn.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Decode subject
                    subject = decode_header(email_message["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    # Get sender
                    sender = email_message["From"]
                    
                    # Get email body
                    body = self.get_email_body(email_message)
                    
                    email_data = {
                        'id': email_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'body': body,
                        'date': email_message["Date"]
                    }
                    
                    new_emails.append(email_data)
                    self.processed_emails.add(email_id.decode())
                    
                    self.logger.info(f"New email from {sender}: {subject[:50]}...")
                    
                except Exception as e:
                    self.logger.warning(f"Error processing email {email_id}: {e}")
                    continue
            
            return new_emails
            
        except Exception as e:
            self.logger.error(f"Error reading emails: {e}")
            return []
    
    def get_email_body(self, email_message) -> str:
        """Extract email body content"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode()
            except:
                body = str(email_message.get_payload())
        
        return body.strip()
    
    def send_custom_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send a custom email to recipient with subject and body."""
        if not self.smtp_conn:
            self.connect_email()
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['email']
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            self.smtp_conn.sendmail(self.config['email']['email'], recipient, msg.as_string())
            self.logger.info(f"Sent custom email to {recipient}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send custom email: {e}")
            return False

    def generate_ai_reply(self, email_data: Dict[str, Any]) -> str:
        """Generate AI reply to email"""
        ai_config = self.config.get('ai', {})
        
        if ai_config.get('enabled', False) and self.gemini_model:
            return self.generate_gemini_reply(email_data)
        else:
            return self.generate_improved_mock_reply(email_data)
    
    def generate_gemini_reply(self, email_data: Dict[str, Any]) -> str:
        """Generate reply using Google Gemini"""
        try:
            sender = email_data.get('sender', 'Unknown')
            subject = email_data.get('subject', 'No Subject')
            body = email_data.get('body', '')[:500]  # Limit body length
            
            # Extract sender name
            sender_name = "there"
            if '<' in sender:
                name_part = sender.split('<')[0].strip()
                if name_part:
                    sender_name = name_part.split()[0]
            
            prompt = f"""You are a professional email assistant for Yash. Write a polite, helpful auto-reply to this email.
            
Sender: {sender_name}
Subject: {subject}
Email content: {body}
            
Write a professional reply that:
1. Acknowledges their message appropriately
2. Is helpful and courteous
3. Indicates you'll respond properly soon (if needed)
4. Keep it brief (2-3 sentences)
5. Sign as "Best regards, Yash"
6. Use proper email formatting with line breaks
            
Reply:"""
            
            response = self.gemini_model.generate_content(prompt)
            reply = response.text.strip()
            
            self.logger.info("Generated Gemini AI reply")
            return reply
            
        except Exception as e:
            self.logger.error(f"Gemini reply generation failed: {e}")
            return self.generate_improved_mock_reply(email_data)
    
    def generate_improved_mock_reply(self, email_data: Dict[str, Any]) -> str:
        """Generate smart mock AI reply with context awareness"""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        sender = email_data.get('sender', '')
        
        # Extract first name from sender
        sender_name = "there"
        if '<' in sender:
            name_part = sender.split('<')[0].strip()
            if name_part:
                sender_name = name_part.split()[0]
        
        # More contextual replies based on content
        content = f"{subject} {body}"
        
        # Dinner/social invitations
        if any(word in content for word in ['dinner', 'lunch', 'coffee', 'drink', 'hang out', 'meet up']):
            reply = f"Dear {sender_name},\\n\\nThank you for the invitation! I'd love to catch up. Let me check my schedule and I'll get back to you shortly with some available times.\\n\\nLooking forward to it!\\n\\nBest regards,\\nYash"
        
        # Availability/scheduling  
        elif any(word in content for word in ['free', 'available', 'time', 'when', 'schedule']):
            reply = f"Dear {sender_name},\\n\\nThanks for reaching out about my availability. I'll review my calendar and send you some time slots that work for both of us.\\n\\nI'll get back to you within a few hours.\\n\\nBest regards,\\nYash"
        
        # Office/work related
        elif any(word in content for word in ['leave', 'office', 'work', 'meeting', 'project']):
            reply = f"Dear {sender_name},\\n\\nThank you for your message regarding work matters. I've received your request and will review it promptly.\\n\\nI'll respond with the necessary information soon.\\n\\nBest regards,\\nYash"
        
        # Meeting requests
        elif any(word in content for word in ['call', 'appointment', 'zoom', 'teams']):
            reply = f"Dear {sender_name},\\n\\nThank you for reaching out about scheduling a meeting. I'll review my calendar and get back to you shortly with my availability.\\n\\nBest regards,\\nYash"
        
        # Project/business related
        elif any(word in content for word in ['business', 'collaboration', 'proposal']):
            reply = f"Dear {sender_name},\\n\\nThank you for your message regarding the business opportunity. I'm interested in learning more about this collaboration.\\n\\nI'll review the details and respond with my thoughts soon.\\n\\nBest regards,\\nYash"
        
        # Urgent matters
        elif any(word in content for word in ['urgent', 'asap', 'emergency', 'immediate', 'important']):
            reply = f"Dear {sender_name},\\n\\nI've received your urgent message and will prioritize reviewing it immediately. You can expect a detailed response within the next hour.\\n\\nBest regards,\\nYash"
        
        # Questions
        elif any(word in content for word in ['question', 'help', 'support', 'how', 'what', 'why', '?']):
            reply = f"Dear {sender_name},\\n\\nThank you for your question. I'll look into this and provide you with a comprehensive answer shortly.\\n\\nBest regards,\\nYash"
        
        # Default professional response
        else:
            reply = f"Dear {sender_name},\\n\\nThank you for your email. I've received your message and will review it carefully. I'll get back to you with a detailed response soon.\\n\\nBest regards,\\nYash"
        
        return reply
        """Generate mock AI reply with better formatting"""
        subject = email_data.get('subject', '').lower()
        sender = email_data.get('sender', '')
        
        # Extract first name from sender
        sender_name = "there"
        if '<' in sender:
            name_part = sender.split('<')[0].strip()
            if name_part:
                sender_name = name_part.split()[0]
        
        # Generate contextual replies with proper line breaks
        if any(word in subject for word in ['meeting', 'schedule', 'appointment']):
            reply = f"Dear {sender_name},\n\nThank you for reaching out about the meeting. I'll review my calendar and get back to you shortly with my availability.\n\nBest regards,\nYash"
        
        elif any(word in subject for word in ['urgent', 'asap', 'important']):
            reply = f"Dear {sender_name},\n\nI've received your urgent message and will prioritize reviewing it. I'll respond with more details within the next few hours.\n\nBest regards,\nYash"
        
        elif any(word in subject for word in ['question', 'help', 'support']):
            reply = f"Dear {sender_name},\n\nThank you for your question. I'll review the details and provide you with a comprehensive response soon.\n\nBest regards,\nYash"
        
        else:
            reply = f"Dear {sender_name},\n\nThank you for your email. I've received your message and will review it carefully. I'll get back to you with a detailed response soon.\n\nBest regards,\nYash"
        
        return reply
    
    def send_reply(self, original_email: Dict[str, Any], reply_text: str) -> bool:
        """Send reply email"""
        if not self.smtp_conn:
            return False
            
        try:
            email_config = self.config['email']
            
            # Create reply message
            msg = MIMEMultipart()
            msg['From'] = email_config['email']
            msg['To'] = original_email['sender']
            msg['Subject'] = f"Re: {original_email['subject']}"
            
            # Add reply text
            msg.attach(MIMEText(reply_text, 'plain'))
            
            # Send email
            text = msg.as_string()
            self.smtp_conn.sendmail(email_config['email'], original_email['sender'], text)
            
            self.logger.info(f"Reply sent to {original_email['sender']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send reply: {e}")
            return False
    
    def process_emails(self):
        """Process new emails and send auto-replies"""
        agent_config = self.config.get('agent', {})
        
        if not agent_config.get('auto_reply', True):
            self.logger.info("Auto-reply is disabled")
            return
        
        new_emails = self.read_new_emails()
        
        if not new_emails:
            return
        
        reply_delay = agent_config.get('reply_delay', 5)
        
        for email_data in new_emails:
            try:
                self.logger.info(f"Generating reply for: {email_data['subject'][:50]}...")
                
                # Generate AI reply
                reply_text = self.generate_ai_reply(email_data)
                
                # Wait before sending (more natural)
                time.sleep(reply_delay)
                
                # Send reply
                if self.send_reply(email_data, reply_text):
                    self.logger.info("Auto-reply sent successfully")
                else:
                    self.logger.error("Failed to send auto-reply")
                    
            except Exception as e:
                self.logger.error(f"Error processing email {email_data.get('id', 'unknown')}: {e}")
                continue
    
    def run(self):
        """Main run loop"""
        self.logger.info("Starting Email to Email AI Agent")
        
        if not self.connect_email():
            self.logger.error("Failed to connect to email. Exiting.")
            return
        
        check_interval = self.config.get('agent', {}).get('check_interval', 30)
        
        self.logger.info(f"Monitoring emails every {check_interval} seconds...")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                self.process_emails()
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping Email Agent...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup connections"""
        try:
            if self.imap_conn:
                self.imap_conn.close()
                self.imap_conn.logout()
            if self.smtp_conn:
                self.smtp_conn.quit()
            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")

def main():
    """Main entry point"""
    print("🤖 Email to Email AI Agent")
    print("=" * 40)
    
    try:
        agent = EmailToEmailAgent()
        agent.run()
    except FileNotFoundError:
        print("\\n📋 Please configure your email settings in config.yaml")
        print("\\n🔑 Gmail App Password Setup:")
        print("1. Go to Google Account Settings")
        print("2. Enable 2-Factor Authentication")  
        print("3. Generate App Password for 'Mail'")
        print("4. Use this 16-character password in config.yaml")
    except Exception as e:
        print(f"\\n❌ Error: {e}")

if __name__ == "__main__":
    main()