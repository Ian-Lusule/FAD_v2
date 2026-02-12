"""
Module for sending analysis reports via email.
Adapted from original Streamlit version.
"""

import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict
import logging
from modules.report_generator import RISK_ADVICE_UI
from config import Config

# Import disclaimer constants from report_generator for consistency
from modules.report_generator import DISCLAIMER_TEXT, DISCLAIMER_LINK

logger = logging.getLogger(__name__)

# New constants for email risk messaging (can be the same as report_generator or adapted)
RISK_WARNING_EMAIL = "Strong indicators of potential risk identified based on a high percentage of negative reviews"
RISK_ADVICE_EMAIL = """
<p>Our analysis is based solely on public user review sentiment and does not involve deep technical analysis of the app's code or official investigative findings. The alert is triggered by your set threshold for negative reviews.</p>
<p>We strongly recommend conducting further independent research and due diligence before downloading, using, or trusting this app with personal information or financial data. If you have concerns, consider reporting the app directly to the Google Play Store or relevant authorities. Look for red flags such as unclear developer history, excessive permissions, or consistent scam reports elsewhere.</p>
"""

def send_analysis_email(
    user_name: str,
    user_email: str,
    app_details: Dict,
    app_id: str,
    filtered_df: pd.DataFrame,
    sentiment_counts: pd.Series,
    positive_pct: float,
    negative_pct: float,
    neutral_pct: float,
    app_rating_score: float,
    playstore_score: float,
    fraud_threshold: float,
    csv_data: bytes,
    pdf_data: bytes,
    sender_email: str,
    sender_password: str,
    smtp_server: str,
    smtp_port: int
) -> bool:
    """
    Sends an analysis report via email.
    
    Args:
        user_name (str): Recipient name.
        user_email (str): Recipient email.
        app_details (Dict): App details.
        app_id (str): App ID.
        filtered_df (pd.DataFrame): Reviews DataFrame.
        sentiment_counts (pd.Series): Sentiment counts.
        positive_pct (float): Positive percentage.
        negative_pct (float): Negative percentage.
        neutral_pct (float): Neutral percentage.
        app_rating_score (float): App rating score.
        playstore_score (float): Play Store score.
        fraud_threshold (float): Fraud threshold.
        csv_data (bytes): CSV file data.
        pdf_data (bytes): PDF file data.
        sender_email (str): Sender email.
        sender_password (str): Sender password.
        smtp_server (str): SMTP server.
        smtp_port (int): SMTP port.
        
    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    try:
        # Load credentials from Config if not provided
        if not sender_email:
            sender_email = Config.MAIL_USERNAME
        if not sender_password:
            sender_password = Config.MAIL_PASSWORD
        if not smtp_server:
            smtp_server = Config.MAIL_SERVER
        if not smtp_port:
            smtp_port = Config.MAIL_PORT
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = user_email
        msg['Subject'] = f"Fraud App Analyzer Report: {app_details.get('title', app_id)}"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Fraud App Analyzer Report</h2>
            <p>Dear {user_name},</p>
            
            <p>Here is your analysis report for <strong>{app_details.get('title', app_id)}</strong>:</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3>App Details</h3>
                <p><strong>App Name:</strong> {app_details.get('title', 'N/A')}</p>
                <p><strong>Developer:</strong> {app_details.get('developer', 'N/A')}</p>
                <p><strong>Installs:</strong> {app_details.get('installs', 'N/A')}</p>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3>Analysis Summary</h3>
                <p><strong>Total Reviews Analyzed:</strong> {len(filtered_df)}</p>
                <p><strong>Positive Sentiment:</strong> {positive_pct:.1f}%</p>
                <p><strong>Negative Sentiment:</strong> {negative_pct:.1f}%</p>
                <p><strong>Neutral Sentiment:</strong> {neutral_pct:.1f}%</p>
                <p><strong>App Rating Score:</strong> {app_rating_score:.1f}%</p>
                <p><strong>Play Store Score:</strong> {playstore_score:.1f}%</p>
                <p><strong>Risk Threshold:</strong> {fraud_threshold}%</p>
            </div>
        """
        
        # Add risk warning if applicable
        if negative_pct > fraud_threshold:
            body += f"""
            <div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 15px 0; border: 1px solid #f5c6cb;">
                <h3 style="color: #721c24;">⚠️ Risk Alert</h3>
                <p><strong>{RISK_WARNING_EMAIL}</strong></p>
                <p>Negative sentiment ({negative_pct:.1f}%) exceeds your threshold of {fraud_threshold}%.</p>
                {RISK_ADVICE_EMAIL}
            </div>
            """
        else:
            body += """
            <div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 15px 0; border: 1px solid #c3e6cb;">
                <h3 style="color: #155724;">✅ No Significant Risk</h3>
                <p>No significant risk indicators found based on your current threshold settings.</p>
            </div>
            """
        
        # Add disclaimer
        body += f"""
            <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin: 15px 0; font-size: 12px;">
                <p><strong>Disclaimer:</strong> {DISCLAIMER_TEXT}</p>
                <p>For more information: <a href="{DISCLAIMER_LINK}">{DISCLAIMER_LINK}</a></p>
            </div>
            
            <p>Please find the detailed reports attached to this email.</p>
            
            <p>Best regards,<br>
            Fraud App Analyzer Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach CSV
        csv_attachment = MIMEApplication(csv_data)
        csv_attachment.add_header('Content-Disposition', 'attachment', 
                                 filename=f'{app_id}_review_analysis.csv')
        msg.attach(csv_attachment)
        
        # Attach PDF
        pdf_attachment = MIMEApplication(pdf_data)
        pdf_attachment.add_header('Content-Disposition', 'attachment',
                                 filename=f'{app_id}_full_app_summary.pdf')
        msg.attach(pdf_attachment)
        
        # Send email. Use SSL for port 465, otherwise use STARTTLS.
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
        
        logger.info(f"Email sent successfully to {user_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Email sending failed: Authentication error")
        return False
    except smtplib.SMTPConnectError:
        logger.error("Email sending failed: Could not connect to SMTP server")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_welcome_email(
    user_email: str,
    user_name: str,
    sender_email: str,
    sender_password: str,
    smtp_server: str,
    smtp_port: int
) -> bool:
    """
    Send welcome email to new users.
    
    Args:
        user_email (str): User email.
        user_name (str): User name.
        sender_email (str): Sender email.
        sender_password (str): Sender password.
        smtp_server (str): SMTP server.
        smtp_port (int): SMTP port.
        
    Returns:
        bool: True if email sent successfully.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = user_email
        msg['Subject'] = 'Welcome to Fraud App Analyzer'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Welcome to Fraud App Analyzer, {user_name}!</h2>
            
            <p>Thank you for registering with Fraud App Analyzer. You can now:</p>
            
            <ul>
                <li>Analyze apps for potential fraud risks</li>
                <li>Save your analysis results</li>
                <li>Compare multiple apps side by side</li>
                <li>Export reports as CSV or PDF</li>
                <li>Receive email reports</li>
            </ul>
            
            <p>Start by visiting our homepage and entering an app name or Play Store URL.</p>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact us through the contact form in your dashboard.</p>
            
            <p>Best regards,<br>
            Fraud App Analyzer Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return False