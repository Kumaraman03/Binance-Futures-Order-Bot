import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY or API_SECRET not found. Check your .env file.")

client = Client(API_KEY, API_SECRET, testnet=True)

# Check account information
account_info = client.futures_account()
print("Futures Account Info:", account_info)
