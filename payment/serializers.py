from rest_framework import serializers
from .models import PaymentTransaction
from courses.serializers import CartSerializer

class PaymentTransactionSerializer(serializers.ModelSerializer):
    cart_detail = CartSerializer(read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = ('id', 'cart', 'user', 'cart_detail', 'amount', 'status',
                 'payment_gateway', 'transaction_id', 'created_at')
        read_only_fields = ('created_at', 'cart_detail',)
