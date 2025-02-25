import pyautogui as pg
import time
import logging
import requests
import imaplib
import email
import yaml
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv('.envrc')

webhook_url = os.environ["SLACK_WEBHOOK_URL"] 
login_email = os.environ["RESPONDIO_EMAIL"]
password = os.environ["RESPONDIO_PASSWORD"]
gmail_login = os.environ["GMAIL_ADDRESS"]
gmail_password = os.environ["GMAIL_APP_PASSWORD"]

# Configure logging at the start of your script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_automation.log'),  # Save logs to file
        logging.StreamHandler()  # Also show logs in console
    ]
)

def load_creds(file_path):
    """Load credentials from YAML file"""
    try:
        with open(file_path, 'r') as file:
            creds = yaml.safe_load(file)
            logging.info("Successfully loaded credentials from YAML")
            return (
                creds.get('user'),
                creds.get('app-password')  # Using app-password instead of regular password
            )
    except Exception as e:
        logging.error(f"Error loading credentials: {str(e)}", exc_info=True)
        raise

def check_for_export_email(creds_file, timeout_minutes=15):
    """
    Check Gmail for UNREAD export completion email using credentials from YAML
    """
    logging.info("Starting to check for unread export completion email")
    
    try:
        # Load credentials
        email_address, app_password = load_creds(creds_file)
        
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, app_password)
        logging.info("Successfully connected to Gmail")
        
        start_time = datetime.now(timezone.utc)
        while datetime.now(timezone.utc) - start_time < timedelta(minutes=timeout_minutes):
            # Select inbox
            mail.select("INBOX")
            
            # Search for UNREAD emails with specific subject
            search_query = 'SUBJECT "Data export request completed for Customer Success | respond.io" UNSEEN'
            _, message_numbers = mail.search(None, search_query)
            
            if message_numbers[0]:
                # Get the latest email's date
                latest_email_id = message_numbers[0].split()[-1]
                _, msg_data = mail.fetch(latest_email_id, "(RFC822)")
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                date_str = message["date"]
                date = email.utils.parsedate_to_datetime(date_str)
                
                # Now both datetimes are timezone-aware
                if datetime.now(timezone.utc) - date < timedelta(minutes=15):
                    logging.info("Unread export completion email found")
                    
                    # Optional: Mark the email as read after finding it
                    mail.store(latest_email_id, '+FLAGS', '\\Seen')
                    logging.info("Marked export completion email as read")
                    
                    mail.logout()
                    return True
            
            # Wait before checking again
            logging.info("Unread export email not found yet, waiting 30 seconds...")
            time.sleep(30)
        
        logging.warning(f"Unread email not found within {timeout_minutes} minutes timeout")
        mail.logout()
        return False
        
    except Exception as e:
        logging.error(f"Error checking email: {str(e)}", exc_info=True)
        return False
    

def send_slack_webhook(principal:str, report_type:str, status:str = "success"):
    """
    Send a notification to Slack Channel during exporting
    """

    # set color and emoji for status
    color = "#36a64f" if status == "success" else "#ff0000" if status == "error" else "#cccccc"
    emoji = ":white_check_mark:" if status == "success" else ":x:" if status == "error" else ":checking:"

    # Prepare common fields
    common_fields = [
        {
            "title": "Status",
            "value": status.title(),
            "short": True
        },
        {
            "title": "Timestamp",
            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "short": True
        }
    ]

    if principal.lower() in {"cron job triggered", "cron job completed", "cron job error", "test run"}:
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": principal,
                    "text": f"{emoji} {report_type}",
                    "fields": common_fields,
                    "footer": "Respondio Export Bot`",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

    else:
        # slack message payload
        payload = {
            "attachments": [
                {
                    "fallback": f"Respondio Data Export - {principal} ({status.title()})",
                    "color": color,
                    "title": f"Respondio Data Export - {principal}",
                    "text": f"{emoji} Export Finished for *{report_type}*",
                    "fields": [
                        {
                            "title": "Task",
                            "value": principal,
                            "short": True
                        },
                        {
                            "title": "Report Type",
                            "value": f"{report_type}",
                            "short": True
                        },
                        *common_fields  # Include common fields
                    ],
                    "footer": "Respondio Export Bot",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send Slack Notification: {str(e)}")  # Use logging instead of print

def send_start_message():
    """Send a start message to Slack when the cron job begins"""
    send_slack_webhook(
        principal="Scraping Start",
        report_type="Respondio Scraping is now running.",
        status="info"
    )

def send_end_message(success: bool):
    """Send a completion message to Slack when the cron job finishes"""
    status = "success" if success else "error"
    completion_message = "Respondio Script finished successfully." if success else "Respondio Export Script encountered an error."
    
    send_slack_webhook(
        principal="Cron Job Completed",
        report_type=completion_message,
        status=status
    )

def open_chrome():
    time.sleep(5)
    logging.info("Opening chrome browser")
    pg.moveTo(800,1000)
    time.sleep(2)
    pg.click()
    time.sleep(2)
    pg.write('google-chrome')
    pg.press('enter')
    time.sleep(20)

def login(email, password):
    has_loggedin = False  # Initialize to False by default
    try:
        logging.info("Starting login process")
        
        # Navigate to login page
        logging.info("Navigating to login URL")
        pg.hotkey("ctrl", 'l')
        time.sleep(3)
        pg.write("https://app.respond.io/user/login")
        time.sleep(2)
        pg.press("enter")
        logging.info("Navigation to login page complete")
        
        # Wait for page load
        logging.info("Waiting for login page to load")
        time.sleep(20)
        
        # Email input
        logging.info("Entering email")
        pg.moveTo(900, 470)
        pg.click()
        time.sleep(2)
        pg.write(email)
        logging.info("Email entered successfully")
        
        # Password input
        logging.info("Entering password")
        pg.press("tab")
        pg.write(password)
        time.sleep(2)
        logging.info("Password entered successfully")
        
        # Submit login
        logging.info("Submitting login form")
        pg.press("enter")
        
        # Wait for login to complete
        logging.info("Waiting for login to process")
        time.sleep(20)
        
        has_loggedin = True
        logging.info("Login process completed successfully")
        send_slack_webhook(principal="Login Complete", report_type="Contacts Export Data", status="In progress")
        
    except Exception as e:
        logging.error(f"Login failed: {str(e)}", exc_info=True)
        has_loggedin = False
        
    finally:
        logging.info(f"Login attempt finished. Success: {has_loggedin}")
        # Mask the email for privacy in logs
        logging.info(f"Attempted login for user: {str(email)}")
        return has_loggedin


        logging.info(f"Download process finished. Success: {download_success}")
        return download_success

def download(email_address, email_password):
    download_success = False
    try:
        logging.info("Starting download process")
        logging.info("Initiating URL navigation")
        
        pg.hotkey('ctrl','l')
        logging.info("Pressed Ctrl+L to focus address bar")
        time.sleep(2)
        
        url = 'https://app.respond.io/space/159614/settings/data_export'
        pg.write(url)
        logging.info(f"Entered URL: {url}")
        time.sleep(2)
        
        pg.press('enter')
        logging.info("Pressed Enter to navigate")
        time.sleep(2)
        logging.info("Waiting for page to load completely")
        time.sleep(20)
        
        logging.info("Triggering contacts export download")
        time.sleep(2)
        pg.moveTo(350,350)
        time.sleep(3)
        pg.click()
        logging.info("Triggered contacts export download")
        send_slack_webhook(principal="Download Triggered", report_type="Contacts Export Data", status="In progress")
        
        # Wait for export completion email
        logging.info("Waiting for export completion email...")
        if check_for_export_email('credentials.yaml'):
            logging.info("Export completion confirmed via email")
            download_success = True
        else:
            logging.error("Export completion email not received within timeout period")
            download_success = False
        
        time.sleep(10)
        logging.info("Downloading exported contacts data")
        pg.hotkey('ctrl','l')
        time.sleep(2)
        pg.press('enter')
        logging.info("Refreshed exports page to download export")
        time.sleep(20)
        pg.moveTo(1550,500)
        time.sleep(2)
        pg.click()
        logging.info("Clicked download button")
        time.sleep(10)
        logging.info("Export file downloaded")
        
        logging.info("Signing out current session")
        time.sleep(4)
        pg.moveTo(30,800)
        time.sleep(2)
        pg.click()
        time.sleep(2)
        pg.moveTo(100,770)
        time.sleep(2)
        pg.click()
        time.sleep(10)
        logging.info("Account signed out")
        
        download_success = True
        send_slack_webhook(principal="Export file downloaded successfully", report_type="Contacts Export Data", status="success")
        

    except Exception as e:
        logging.error(f"Download error occurred: {str(e)}", exc_info=True)
        download_success = False
    
    finally:
        logging.info(f"Download process finished. Success: {download_success}")
        return download_success

if __name__ == "__main__":
    logging.info(f"Started PyAutoGUI Script for Respondio Scraping")
    send_start_message()
    open_chrome()
    log_in = login(login_email, password)
    if log_in:
        logging.info("Logged in successfully, transition to export")
        download = download(gmail_login,gmail_password)
        if download:
            send_end_message(True)
        else:
            send_end_message(False)
    else:
        logging.info("Logged in failed, aborting process")
        exit

# logging.info("Started PyAutoGUI Script to trigger download")
# time.sleep(5)
# pg.moveTo(900,750)
# time.sleep(5)
# pg.click()
# pg.write(f"/home/dhon_bobis/shopee/venv/bin/python /home/dhon_bobis/shopee/respondio_download.py")
# pg.press('enter')