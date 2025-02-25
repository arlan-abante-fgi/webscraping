from utils.targets.bq_utils import TargetGoogleCloudStorage
from datetime import datetime
import pandas as pd
import numpy as np
import fastparquet as fp
import os
import time
import traceback
import logging
import glob
import os 
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('.envrc')

# Get current timestamp as datetime object
current_time = datetime.now()

# Format as string (common formats)
timestamp_str = current_time.strftime('%Y%m%d_%H%M%S')  # Example: 20240321_143022
timestamp_iso = current_time.isoformat()  # Example: 2024-03-21T14:30:22.123456
timestamp_simple = current_time.strftime('%Y-%m-%d %H:%M:%S')  # Example: 2024-03-21 14:30:22

# Get Unix timestamp (seconds since epoch)
unix_timestamp = int(time.time())  # Example: 1711031422

test_target = TargetGoogleCloudStorage(
    name=os.environ["TARGET_NAME"],
    service_account_file=os.environ["SERVICE_ACCOUNT_FILE"]
)

current_date = datetime.today().strftime('%Y-%m-%d')

has_auth = test_target.authenticate()

dir_folder = '../shopee/'

print(f'Authenticated: {has_auth}')

# test_target.upload(
#     source_file=dir_path,  # Use file_path parameter for single file upload
#     bucket='test_ws_datapipeline',
#     file_path=f'shopee_test/{filename}_{unix_timestamp}.csv'  # Include the desired filename in GCS
# )

# bucket_name = os.environ['GCS_BUCKET_NAME']
# blob_name = os.environ['GCS_BLOB_NAME']

bucket_name = 'test_ws_datapipeline'
blob_name = 'shopee_test'

test_target.upload_local_directory_to_gcs(
    directory_path=dir_folder,
    bucket_name='test_ws_datapipeline',
    blob_name=f'shopee_test/{current_date}/Test/' # test upload: test-ws-datapipeline/shopee_test/
)
# update to test blob name
