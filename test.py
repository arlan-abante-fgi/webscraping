# import os
# print("Current files in directory:", os.listdir("/home/dhon_bobis/shopee/data/Focus Global"))

import os
from pathlib import Path
import pandas as pd
# from google.cloud import storage
# from google.cloud import bigquery
# from google.oauth2 import service_account
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv('.envrc')

print(os.environ["RESPONDIO_PASSWORD"])


downloads_path = Path.home() / "Downloads"
csv_files = list(downloads_path.glob('*.csv'))
print(downloads_path)
print(csv_files)