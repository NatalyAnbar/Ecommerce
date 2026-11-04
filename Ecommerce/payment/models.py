"""Payments for orders, handled by a simulated payment gateway."""

from uuid import uuid4
from django.db import models
from order.models import Order


class Payment(models.Model):
    """
    One attempt to pay for an order.

    An order can have several attempts (a declined card, then another card),
    but only one of them can succeed.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'

    # An order that was paid for must never disappear from the records
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    # Copied from the order when paying, so it records exactly what was charged
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    # The gateway's reference for this payment
    transaction_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    # Only the last four digits are kept; the full card number is never stored
    card_last4 = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Failed attempts are unlimited, but an order is charged at most once
            models.UniqueConstraint(
                fields=['order'],
                condition=models.Q(status='succeeded'),
                name='one_successful_payment_per_order',
            ),
        ]

    def __str__(self):
        return f'{self.amount} for order {self.order_id} ({self.status})'