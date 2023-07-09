from binance.client import Client
import creds

def get_spot_client():
    client = Client(api_key=creds.api_key, api_secret=creds.api_secret)
    client.API_URL = creds.url
    return client