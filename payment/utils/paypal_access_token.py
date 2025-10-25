import requests
import base64
from decouple import config

def get_paypal_access_token():
    """
    Helper function to get access token from PayPal API.
    """
    client_id = config('PAYPAL_CLIENT_ID')
    client_secret = config('PAYPAL_CLIENT_SECRET')
    url = config('PAYPAL_BASE_URL', 'https://api.sandbox.paypal.com') + '/v1/oauth2/token'


    # Prepare headers with Base64 encoded credentials
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {credentials}'
    }
    data = {'grant_type': 'client_credentials'}

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises an exception for bad status codes
    return response.json()['access_token']
