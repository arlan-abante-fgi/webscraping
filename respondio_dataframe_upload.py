from pathlib import Path
import pandas as pd
import os
import logging
import requests
from google.cloud import storage
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('.envrc')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# get credentials from service account file
def get_credentials(key_path):
    """Initialize credentials from service account"""
    return service_account.Credentials.from_service_account_file(
        key_path,
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/bigquery",
        ]
    )

def load_to_bigquery(bq_client, df, table_id):
    """Helper function to load a dataframe to BigQuery, replacing existing data"""
    if df.empty:
        logger.info("No data to load")
        return False

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE  # This will replace existing data
    )
    
    try:
        logger.info("Starting data load to BigQuery...")
        job = bq_client.load_table_from_dataframe(
            df,
            table_id,
            job_config=job_config
        )
        job.result()  # Wait for the job to complete
        
        table = bq_client.get_table(table_id)
        logger.info(f"\nSuccessfully replaced table data with {len(df)} rows")
        logger.info(f"Total rows in table: {table.num_rows}")
        return True
        
    except Exception as e:
        logger.error(f"Error loading data to BigQuery: {str(e)}")
        return False

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
                    "footer": "Respondio Data Uploader Bot`",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

    else:
        # slack message payload
        payload = {
            "attachments": [
                {
                    "fallback": f"Respondio Data Uploader - {principal} ({status.title()})",
                    "color": color,
                    "title": f"Respondio Data Uploader - {principal}",
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
        report_type="Data Upload Script is now running.",
        status="info"
    )

def send_end_message(success: bool):
    """Send a completion message to Slack when the cron job finishes"""
    status = "success" if success else "error"
    completion_message = "Data Upload Script finished successfully." if success else "Data Upload Script encountered an error."
    
    send_slack_webhook(
        principal="Cron Job Completed",
        report_type=completion_message,
        status=status
    )

warehouse_name = os.environ["BQ_WAREHOUSE_NAME"]
dataset_name = os.environ["RESPONDIO_DATASET_NAME"]
table_name = os.environ["RESPONDIO_TABLE_NAME"]
key_path = os.environ["SERVICE_ACCOUNT_FILE"]

downloads_path = Path.home() / "Downloads"
print(downloads_path)
csv_files = list(downloads_path.glob('*.csv'))

logger.info(f"Starting BQ Data Upload...")
send_start_message()

if csv_files:
    latest_file = max(csv_files, key=lambda file: file.stat().st_mtime)
    logger.info(f"Most recent file: {latest_file}")
    exported_data = pd.read_csv(latest_file)
    exported_data['LastInteractionTime'] = pd.to_datetime(exported_data['LastInteractionTime'])
    exported_data = exported_data.sort_values('LastInteractionTime', ascending=False)
    exported_data = exported_data.rename(columns={"Customer Concern": "CustomerConcern"})
    clean_data = exported_data.fillna('')

    clean_data = clean_data.astype(str)
    logger.info("Data export cleaned")
    # logger.info("Clean data:")
    # logger.info(clean_data)

    # Initialize BigQuery client
    try:
        logger.info("Initializing BigQuery client...")
        credentials = get_credentials(key_path)
        bq_client = bigquery.Client(credentials=credentials)
        
        # Construct table_id
        table_id = f'{warehouse_name}.{dataset_name}.{table_name}'
        
        logger.info(f"\nAttempting to replace data in table: {table_id}")
        success = load_to_bigquery(bq_client, clean_data, table_id)
        
        if success:
            logger.info("Table data successfully replaced in BigQuery")
            os.remove(latest_file)
            logger.info("Removed latest downloaded file")
            send_slack_webhook(principal="Data Uploaded Successfully", report_type="Contacts Export Data", status="success")
            send_end_message(True)
        else:
            logger.error("Failed to replace data in BigQuery")
            send_slack_webhook(principal="Data Failed to Upload", report_type="Contacts Export Data", status="error")
            send_end_message(False)
            
    except Exception as e:
        logger.error(f"Error initializing BigQuery client: {str(e)}")
        send_slack_webhook(principal="BigQuery Client Corrupted", report_type="Contacts Export Data", status="error")
        send_end_message(False)
else:
    logger.warning("No CSV files found in Downloads directory")
    send_slack_webhook(principal="No Export File Found", report_type="Contacts Export Data", status="error")
    send_end_message(False)

logger.info("Data upload process completed")