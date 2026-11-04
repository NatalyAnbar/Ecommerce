from rest_framework import serializers
from uuid import uuid4
from . import models


class PaySerializer(serializers.Serializer):
    """What the client sends to pay: only the card number, never stored."""

    # 16 digits exactly; used once to decide the payment, then discarded
    card_number = serializers.RegexField(r'^\d{16}$', write_only=True)


    def validate(self, attrs):
        """Reject early when the order already has a successful payment."""
        order_pk = self.context['order_pk']

        if models.Payment.objects.filter(
            order_id=order_pk, status=models.Payment.Status.SUCCEEDED
            ).exists():
            raise serializers.ValidationError('This order has already been paid.')
        
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """A payment attempt as shown in responses."""
    
    class Meta:
        model = models.Payment
        fields = ['transaction_id','amount','status','card_last4','created_at']
        read_only_fields = fields

