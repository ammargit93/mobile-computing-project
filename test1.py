# Send email
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

email_address = os.getenv("EMAIL")
email_password = os.getenv("PASSWORD")
print(email_address, email_password)
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = email_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.sendmail(email_address, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

send_email(email_address, "Test Email", "This is a test email.")
