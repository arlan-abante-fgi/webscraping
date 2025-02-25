from json import dumps
from enum import Enum
from random import choices
from string import ascii_letters, digits
from colorama import Fore, init
from hashlib import md5, sha256
from bs4 import BeautifulSoup
import requests
import os
import pickle

def randomize_token() -> str:
    return ''.join(choices(ascii_letters + digits, k=32))

session = requests.Session()

login_url = "https://shopee.ph/seller/login"
response = session.get(login_url)

# Check if the request was successful
if response.status_code == 200:
    print("Login page fetched successfully.")
else:
    print(f"Failed to fetch login page, status code: {response.status_code}")

csrf_token = session.cookies.get('csrftoken')

if not csrf_token:
    soup = BeautifulSoup(response.text, 'lxml')
    
    csrf_token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    
    if csrf_token_input:
        csrf_token = csrf_token_input.get('value')

if csrf_token:
    print(f"CSRF token found: {csrf_token}")
else:
    print("CSRF token not found.")

response = session.get(
    url="https://seller.shopee.ph/api/mydata/v2/product/overview/export/?start_ts=1729008000&end_ts=1729062000&period=real_time",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "If-None-Match": "*",
        "Referer": "https://shopee.ph/seller/login",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
)

cookies = session.cookies.get_dict()
for cookie in cookies:
    print(f"{cookie.name}: {cookie.value}")

print(response)
# token = randomize_token()

# headers = {
#        "accept": "application/json",
#         "content-type": "application/json",
#         "if-none-match-": "*",
#         "referer": "https://shopee.ph/seller/login",
#         "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
#         "x-csrftoken": token,
#         "x-requested-with": "XMLHttpRequest"
# }            

# session = requests.Session()
# # session.post("https://shopee.ph/seller/login")

# session.cookies.set("csrftoken", token)

# username = 'colemanphilippines'
# password = 'FGInc.2017!'
# password = md5(password.encode()).hexdigest()
# password = sha256(password.encode()).hexdigest()
# print(password)

# resp = session.post(
#     url="https://shopee.ph/api/v4/account/login_by_password",
#     headers=headers,
#     json={
#         "username": username,
#         "password": password,
#         "support_ivs": True,
#         "ivs_token": "U2FsdGVkX1+c89ahk2/jqoqelc14IWEfvVCSDZJJNoFVM0Wc24N6IYF+zPAK6Bhm4gEwAi7DaIaLrWTW374RFHSB1C5o0WRr25+fr1a5+a076gNgnLeKnSldU/K7lIabpRf5uAsxfcCrm6HWoblbwW9v6h0O5x9dueMQFCh9K9LH6X03gNa9ysBEo1r0utdI5sHJEOSCrveH5isfpQcyLQJHmog/JOmcCzXPbPEbyYAt1BrN2j6l0LEWHaRdKsRYpM2Wo7K5NVonjNxj5QgaGyPJdSIMNrCBnndK/OV//5D3F24WvUb4T3QfPDUbUEAOZCPXGxIJ/8PYXTirkuM4VA=="
#     },
#     cookies=session.cookies
# )


# data = resp.json()
# print(f"Status Code: {resp.status_code}")
# print(f"Response Content: {resp.text}")
# print(data)


# response = session.post("https://shopee.ph/seller/login")

# # Retrieve the cookies from the session
# cookies = session.cookies

# # Print the cookies
# for cookie in cookies:
#     print(f"{cookie.name}: {cookie.value}")