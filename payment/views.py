from rest_framework.views import APIView
from rest_framework.response import Response
from .utils.paypal_order import create_paypal_order
from .serializers import PaymentTransactionSerializer
from decimal import Decimal
from .utils.paypal_access_token import get_paypal_access_token
from .models import PaymentTransaction
import requests
from decouple import config
from rest_framework import permissions, status
import stripe
from decouple import config
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from courses.models import Cart
from django.views import View
from django.http import JsonResponse
import json
import hmac
import hashlib
import base64

class CreatePayPalOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            userCart = request.user.cart
            amount = userCart.get_total_price()

            response = create_paypal_order(str(amount))

            serializer = PaymentTransactionSerializer(data={
                'cart': userCart.id,
                'amount': amount,
                'payment_gateway': "pay_pal",
                'transaction_id': response['id'],
                'user': request.user.id
            })
            if serializer.is_valid():
                print("payment transaksi saved...")
                serializer.save()
            else:
                print("serializer errors:", serializer.errors)
                return Response(serializer.errors, status=400)

            return Response(response)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class CapturePayPalOrderView(APIView):
    """
    Captures a PayPal order after customer approval.
    """
    def post(self, request):
        access_token = get_paypal_access_token()
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Order ID is required'}, status=400)

        try:
            capture_url = f"{config('PAYPAL_BASE_URL', 'https://api.sandbox.paypal.com')}/v2/checkout/orders/{order_id}/capture"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }

            response = requests.post(capture_url, headers=headers, json={})
            response_data = response.json()

            if response.status_code == 201:
                return Response({
                    'status': 'success'
                })
            else:
                payment = PaymentTransaction.objects.filter(transaction_id=order_id)
                if payment.exists():
                    payment.update(status="failed")

                error_message = response_data.get('message', 'Capture failed')
                return Response({'error': error_message}, status=400)

        except requests.exceptions.RequestException as e:
            return Response({'error': 'Failed to capture payment'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PayPalWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            # Ambil body dan headers
            raw_body = request.body
            body = raw_body.decode('utf-8')
            data = json.loads(body)

            required_headers = [
                    'PAYPAL-TRANSMISSION-ID',
                    'PAYPAL-TRANSMISSION-TIME',
                    'PAYPAL-TRANSMISSION-SIG',
                    'PAYPAL-AUTH-ALGO'
                ]

            for header in required_headers:
                if not request.headers.get(header):
                    return Response(
                        {"error": f"Missing required header: {header}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            transmission_id = request.headers.get('PAYPAL-TRANSMISSION-ID')
            transmission_time = request.headers.get('PAYPAL-TRANSMISSION-TIME')
            transmission_sig = request.headers.get('PAYPAL-TRANSMISSION-SIG')
            auth_algo = request.headers.get('PAYPAL-AUTH-ALGO')
            cert_url = request.headers.get('PAYPAL-CERT-URL')
            webhook_id = config("PAYPAL_WEBHOOKS_ID")

            payload = {
                "transmission_id": transmission_id,
                "transmission_time": transmission_time,
                "transmission_sig": transmission_sig,
                "auth_algo": auth_algo,
                "webhook_id": webhook_id,
                "cert_url": cert_url,
                "webhook_event": data
            }

            access_token = get_paypal_access_token()
            base_url = config("PAYPAL_BASE_URL")
            verify_url = f"{base_url}/v1/notifications/verify-webhook-signature"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }

            response = requests.post(verify_url, headers=headers, json=payload)
            verification_result = response.json()

            if verification_result == "FAILURE":
                return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

            # Tangani event
            event_type = data.get("event_type")

            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                order_id = data.get("resource", {}).get("supplementary_data", {}).get("related_ids", {}).get("order_id")
                payment = PaymentTransaction.objects.get(transaction_id=order_id)

                serializer = PaymentTransactionSerializer(payment, data={'status': 'success'}, partial=True)

                if serializer.is_valid():
                    serializer.save()

                payment.cart.items.filter(status="in_cart").update(status="sold")
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                order_id = data.get("resource", {}).get("supplementary_data", {}).get("related_ids", {}).get("order_id")
                payment = PaymentTransaction.objects.filter(transaction_id=order_id)
                if payment.exists():
                    payment.update(status="failed")

            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

stripe.api_key = config('STRIPE_SECRET_KEY')

class CreateStrpieCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            cart = request.user.cart

            items = []

            for item in cart.items.filter(status="in_cart"):
                items.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': item.course.title,
                            },
                            'unit_amount': int(item.course.price  * 100),
                        },
                        'quantity': 1,
                    }
                )

            # Create Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=items,
                mode='payment',
                success_url='http://localhost:5173/checkout/success',
                cancel_url='http://localhost:5173/checkout/fail',
                # Link the session to our internal CartItem ID
                client_reference_id=cart.id
            )

            # DO NOT create a Payment object here.
            # We will create it in the webhook after payment is confirmed.

            return Response({
                'sessionId': checkout_session.id,
                'url': checkout_session.url
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Class-Based View to handle Stripe webhooks
    """

    authentication_classes = []  # Penting: nonaktifkan autentikasi
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        webhookSecret = config('STRIPE_WEBHOOK_SECRET')

        try:
            # Verify webhook event
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhookSecret
            )
        except ValueError as e:
            # Invalid payload
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return JsonResponse({'error': 'Invalid signature'}, status=401)

        print(f"eventt: {event['type']}")

        # Handle event based on type
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_session_completed(session)

        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self.handle_payment_intent_succeeded(payment_intent)

        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self.handle_payment_intent_payment_failed(payment_intent)

        return JsonResponse({'status': 'processed'}, status=200)

    def handle_checkout_session_completed(self, session):
        """
        Handler for event checkout.session.completed
        This is where the order should be fulfilled.
        """
        cart_id = session.get('client_reference_id')
        payment_intent_id = session.get('payment_intent')

        if not cart_id:
            print("Error: client_reference_id not found in session.")
            return

        try:
            cartUser = Cart.objects.get(id=cart_id)
            payment = PaymentTransaction.objects.create(
                transaction_id=payment_intent_id,
                amount=session.get('amount_total') / 100.0, # Stripe returns amount in cents
                payment_gateway='stripe',
                user=cartUser.user,
                status='success',
                cart=cartUser
            )

            payment.cart.items.filter(status="in_cart").update(status="sold")

        except Cart.DoesNotExist:
            print(f"ERROR: CartItem with id={cart_id} does not exist.")
        except Exception as e:
            print(f"An error occurred during fulfillment: {e}")

    def handle_payment_intent_succeeded(self, payment_intent):
        """
        Handler for event payment_intent.succeeded
        """

        try:
            payment = PaymentTransaction.objects.get(transaction_id=payment_intent['id'])
            if payment.exists():
                payment.update(status="success")
            print(f"Payment intent succeeded: {payment_intent['id']}")
        except Exception as e:
            print(f"error: {e}")

    def handle_payment_intent_payment_failed(self, payment_intent):
        """
        Handler for event payment_intent.payment_failed
        """
        # Find the payment record and mark it as failed.
        payment = PaymentTransaction.objects.filter(transaction_id=payment_intent['id'])
        if payment.exists():
            payment.update(status="failed")
        print(f"Payment intent failed: {payment_intent['id']}")
