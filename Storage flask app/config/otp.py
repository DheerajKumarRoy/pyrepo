import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send(user_email,username,resetURL,otp):

    # Email configuration
    sender_email = config.sender_email
    password = config.password

    # Create a multipart message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = user_email
    message['Subject'] = 'Password Reset OTP'

    # Add body to email
    body = f'''
Dear {username},

You have requested to reset your password for your DDRIVE account.

Your OTP (One-Time Password) for resetting the password is:   {otp}

Please use this OTP to verify your identity and proceed with the password reset process.
                                    OR
click here: {resetURL}

NOTE: This OTP is valid for 10 minutes.

If you didn't initiate this password reset request, please ignore this email.

Thank you,
DDRIVE
'''

    message.attach(MIMEText(body, 'plain'))

    # Connect to Gmail's SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)  # Login to Gmail SMTP server
        text = message.as_string()
        server.sendmail(sender_email, user_email, text)  # Send the email
