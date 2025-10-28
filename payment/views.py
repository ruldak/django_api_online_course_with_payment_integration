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
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Order ID is required'}, status=400)

        try:
            access_token = get_paypal_access_token()
            capture_url = f"{config('PAYPAL_BASE_URL', 'https://api.sandbox.paypal.com')}/v2/checkout/orders/{order_id}/capture"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }

            response = requests.post(capture_url, headers=headers)
            response_data = response.json()

            if response.status_code == 201:
                # Pembayaran sukses

                paymentTransaction = PaymentTransaction.objects.get(transaction_id=order_id)

                serializer = PaymentTransactionSerializer(paymentTransaction, data={'status': 'success'}, partial=True)

                if serializer.is_valid():
                    serializer.save()

                return Response({
                    'status': 'success',
                    'message': 'Payment captured successfully',
                    'paypal_data': response_data  # Berisi ID transaksi dll.
                })
            else:
                # Penangkapan pembayaran gagal
                # Update status order di database: 'FAILED'
                error_message = response_data.get('message', 'Capture failed')
                return Response({'error': error_message}, status=400)

        except requests.exceptions.RequestException as e:
            return Response({'error': 'Failed to capture payment'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PayPalWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Ambil body dan headers
        body = request.body
        data = json.loads(body.decode('utf-8'))

        transmission_id = request.headers.get('PAYPAL-TRANSMISSION-ID')
        transmission_time = request.headers.get('PAYPAL-TRANSMISSION-TIME')
        transmission_sig = request.headers.get('PAYPAL-TRANSMISSION-SIG')
        auth_algo = request.headers.get('PAYPAL-AUTH-ALGO')
        webhook_id = config("PAYPAL_WEBHOOKS_ID")

        # Buat signature base string
        message = f"{transmission_id}|{transmission_time}|{webhook_id}|{body.decode('utf-8')}"
        secret = config("PAYPAL_CLIENT_SECRET").encode('utf-8')

        # HMAC-SHA256 signature
        calculated_sig = base64.b64encode(hmac.new(secret, message.encode('utf-8'), hashlib.sha256).digest()).decode()

        if calculated_sig != transmission_sig:
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Tangani event
        event_type = data.get("event_type")
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            print("Payment capture completed:", data.get("resource"))
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            print("payment capture denied")
        elif event_type == "PAYMENT.ORDER.CANCELLED":
            print("payment order cancelled")

        return Response({"status": "success"}, status=status.HTTP_200_OK)

stripe.api_key = config('STRIPE_SECRET_KEY')

class CreateStrpieCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            cart = request.user.cart

            items = []

            for item in cart.items.all():
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
                # payment_method_types=['card'],
                line_items=items,
                mode='payment',
                success_url='https://www.tutorialrepublic.com/snippets/designs/elegant-success-modal.png',
                cancel_url='https://cdn3.vectorstock.com/i/1000x1000/50/27/cancel-red-grunge-round-vintage-rubber-stamp-vector-9145027.jpg',
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
            # Create the Payment record now that payment is confirmed
            PaymentTransaction.objects.create(
                transaction_id=payment_intent_id,
                amount=session.get('amount_total') / 100.0, # Stripe returns amount in cents
                payment_gateway='stripe',
                user=cartUser.user,
                status='success',
                cart=cartUser
            )

        except Cart.DoesNotExist:
            print(f"ERROR: CartItem with id={cart_id} does not exist.")
        except Exception as e:
            print(f"An error occurred during fulfillment: {e}")

    def handle_payment_intent_succeeded(self, payment_intent):
        """
        Handler for event payment_intent.succeeded
        """

        payment = PaymentTransaction.objects.filter(transaction_id=payment_intent['id'])
        if payment.exists():
            payment.update(status="success")
        print(f"Payment intent succeeded: {payment_intent['id']}")

    def handle_payment_intent_payment_failed(self, payment_intent):
        """
        Handler for event payment_intent.payment_failed
        """
        # Find the payment record and mark it as failed.
        payment = PaymentTransaction.objects.filter(transaction_id=payment_intent['id'])
        if payment.exists():
            payment.update(status="failed")
        print(f"Payment intent failed: {payment_intent['id']}")
