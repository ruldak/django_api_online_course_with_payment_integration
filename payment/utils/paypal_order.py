from .paypal_access_token import get_paypal_access_token
from decouple import config
import requests

def create_paypal_order(amount):
    try:
        access_token = get_paypal_access_token()
        paypal_url = config('PAYPAL_BASE_URL', 'https://api.sandbox.paypal.com') + '/v2/checkout/orders'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        # Data payload untuk membuat pesanan di PayPal
        order_data = {
            "intent": "CAPTURE",  # atau "AUTHORIZE"
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": amount  # Amount from request
                }
            }],
            "application_context": {
                "brand_name": "Online Course",
                "return_url": "https://www.tutorialrepublic.com/snippets/designs/elegant-success-modal.png",
                "cancel_url": "https://cdn3.vectorstock.com/i/1000x1000/50/27/cancel-red-grunge-round-vintage-rubber-stamp-vector-9145027.jpg"
            }
        }

        response = requests.post(paypal_url, json=order_data, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        # Cari link approval untuk redirect user
        approval_link = next(link['href'] for link in response_data['links'] if link['rel'] == 'approve')

        # Simpan ID pesanan (response_data['id']) di database jika diperlukan
        return {
            'id': response_data['id'],
            'status': response_data['status'],
            'approval_url': approval_link
        }

    except requests.exceptions.RequestException as e:
        # Handle errors from PayPal API
        raise Exception('Failed to create PayPal order')
