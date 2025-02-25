from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from email import message_from_bytes
from utils.file_relocator import FileRelocator
from utils.targets.bq_utils import TargetGoogleCloudStorage
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import time
import imaplib
import yaml
import logging
import pandas as pd
import json
import re
import os
import requests
from dotenv import load_dotenv

load_dotenv('.envrc')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

email_login = os.environ["RESPONDIO_EMAIL"]
password = os.environ["RESPONDIO_PASSWORD"]


def send_slack_webhook(principal:str, report_type:str, status:str = "success"):
    """
    Send a notification to Slack Channel during exporting
    """

    webhook_url = os.environ['SLACK_WEBHOOK_URL']

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

    if principal.lower() in {"cron job triggered", "cron job completed", "cron job error"}:
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
        principal="Cron Job Triggered",
        report_type="Respondio Export Script is now running.",
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

def setup_driver_for_vm():
    chrome_options = Options()
    
    # Resource management
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--disable-renderer-backgrounding')
    # chrome_options.add_argument('--memory-pressure-off')
    # chrome_options.add_argument('--single-process')
    # chrome_options.add_argument('--disable-application-cache')
    # chrome_options.add_argument('--disk-cache-size=1')
    # chrome_options.add_argument('--media-cache-size=1')
    # chrome_options.add_argument('--js-flags="--max-old-space-size=2048"')
    
    # Disable unnecessary features
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-plugins')
    # chrome_options.add_argument('--disable-logging')
    
    # service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver

def navigate_to_login(driver, max_attempts=5):
    attempt = 0
    while attempt < max_attempts:
        try:
            logger.info(f"Attempt {attempt + 1}/{max_attempts} - Navigating to login page...")
            driver.get('https://app.respond.io/user/login')
            time.sleep(30)
            
            # Wait for either login form or error page
            wait = WebDriverWait(driver, 20)
            try:
                # Check if login form is present
                login_form = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"][name="field_2"]'))
                )
                logger.info("Successfully loaded login page")
                return True
            except TimeoutException:
                # If error page appears, refresh
                logger.warning("Page load error detected, refreshing...")
                driver.refresh()
                time.sleep(10)
                
        except WebDriverException as e:
            logger.error(f"Browser error on attempt {attempt + 1}: {str(e)}")
            try:
                driver.refresh()
            except:
                logger.error("Refresh failed, waiting before retry...")
            time.sleep(10)  # Longer wait after error
            
        attempt += 1
        
    logger.error("Failed to load login page after maximum attempts")
    return False


# Usage
driver = setup_driver_for_vm()

# Usage in your script
if navigate_to_login(driver):
    # send_start_message()
    logger.info("Attempting login...")
    email_input = WebDriverWait(driver,10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"][name="field_2"]'))
    )
    time.sleep(5)
    email_input.send_keys(email_login)
    logger.info("Email entered")
    time.sleep(5)

    password_input = WebDriverWait(driver,10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'input[type="password"][name="field_3"]'))
    )
    time.sleep(5)
    password_input.send_keys(password)
    logger.info("Password entered")
    time.sleep(5)

    login_button = WebDriverWait(driver,10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-pw="btn-signin"]'))
    )
    time.sleep(5)
    login_button.click()
    logger.info("Login button clicked")
    time.sleep(10)

    logger.info("Navigating to data export page...")
    driver.get(r'https://app.respond.io/space/159614/settings/data_export')
    time.sleep(30)
    # time.sleep(10)
    # driver.get(r'https://app.respond.io/space/159614/settings/data_export')
    # driver.refresh()

    time.sleep(15)

    logger.info("Clicking export button...")
    time.sleep(10)
    export_button = WebDriverWait(driver,20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'[data-pw="btn-exp-data"]'))
    )
    # export_button.click()

    # Modified section for handling the table and download
    max_attempts = 30  # Maximum number of refresh attempts
    attempt = 0

    logger.info("Starting export and download process...")
    max_attempts = 30
    attempt = 0
    download_successful = False  # Flag to track if download succeeded

    while attempt < max_attempts and not download_successful:
        try:
            logger.info(f"Attempt {attempt + 1} of {max_attempts}")
            
            # First, click the export button to generate new data
            logger.info("Clicking export button to generate new data...")
            export_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-pw="btn-exp-data"]'))
            )
            export_button.click()
            logger.info("Export button clicked successfully")
            send_slack_webhook(principal="Export Triggered", report_type="Contacts Export Data", status="In progress")
            
            # Now enter the loop to wait for the download to be ready
            logger.info("Starting to check for download readiness...")
            while attempt < max_attempts and not download_successful:
                try:
                    # Refresh first to get latest status
                    logger.info("Clicking refresh button...")
                    refresh_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-pw="btn-refresh"]'))
                    )
                    refresh_button.click()
                    time.sleep(2)  # Wait for refresh to complete
                    
                    # Check first row for download link
                    logger.info("Checking first row for download link...")
                    tbody = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.vue3-easy-data-table__body"))
                    )
                    first_row = tbody.find_element(By.TAG_NAME, "tr")
                    
                    try:
                        anchor = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "tbody.vue3-easy-data-table__body > tr:first-child a[target='_blank']"))
                        )
                        
                        if anchor.is_displayed() and "(Download)" in anchor.text:
                            logger.info("Download link found and is ready")
                            try:
                                logger.info("Attempting to click download link...")
                                anchor.click()
                                logger.info("Download link clicked successfully")
                                download_successful = True
                                send_slack_webhook(principal="Export file downloaded successfully", report_type="Contacts Export Data", status="success")
                                break  # Exit inner loop
                            except ElementNotInteractableException:
                                try:
                                    logger.info("Regular click failed, trying JavaScript click...")
                                    driver.execute_script("arguments[0].click();", anchor)
                                    logger.info("JavaScript click successful")
                                    download_successful = True
                                    break  # Exit inner loop
                                except:
                                    logger.info("JavaScript click failed, trying ActionChains...")
                                    actions = ActionChains(driver)
                                    actions.move_to_element(anchor).click().perform()
                                    logger.info("ActionChains click successful")
                                    download_successful = True
                                    break  # Exit inner loop
                        else:
                            logger.info("Export still processing, waiting...")
                            
                    except (TimeoutException, NoSuchElementException) as e:
                        logger.info(f"Download not ready yet: {str(e)}")
                        # send_slack_webhook(principal="Download attempt timed out", report_type="Contacts Export Data", status="error")
                    
                except StaleElementReferenceException as e:
                    logger.warning(f"Encountered stale element: {str(e)}")
                    send_slack_webhook(principal="Stale element encountered", report_type="Contacts Export Data", status="error")
                    continue
                    
                attempt += 1
                time.sleep(5)  # Wait between checks
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            attempt += 1

    if download_successful:
        logger.info("Download completed successfully")
        send_end_message(True)
    else:
        logger.error("Failed to complete export and download after maximum attempts")
        send_end_message(False)
else:
    logger.error("Could not proceed with login due to page load issues")


logger.info("Script execution completed")