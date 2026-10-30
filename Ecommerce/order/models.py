from django.db import models
from django.conf import settings
from django.core import validators
from decimal import Decimal
from store.models import Product


class Order(models.Model):
    """A customer's purchase: a snapshot of their cart at checkout."""

    class Status(models.TextChoices):
        PENDING = 'pending' , 'Pending'
        PAID = 'paid' , 'Paid'
        CANCELLED = 'cancelled' , 'Cancelled'

    # One user can have many orders, so this is a ForeignKey, not a OneToOne like the cart.
    user = models.ForeignKey(settings.AUTH_USER_MODEL , 
                             on_delete = models.CASCADE ,
                             related_name = 'orders')

    # Every order starts as pending and later becomes paid or cancelled.
    status = models.CharField(
        max_length = 20 ,
        choices = Status.choices ,
        default = Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} by {self.user}'

    @property
    def total_price(self) -> Decimal:
        """Sum of all lines, using the prices saved at checkout."""
        items = self.order_items.all()
        return sum(item.total_price for item in items)



class OrderItem(models.Model):
    """One line of an order, with the price the customer paid."""

    order = models.ForeignKey(Order , 
                              on_delete = models.CASCADE ,
                              related_name = 'order_items')
    
    # PROTECT: a product that appears in an order can't be deleted,
    # so past orders always stay complete.
    product = models.ForeignKey(Product ,
                                on_delete = models.PROTECT ,
                                related_name = 'order_items')

    # Copied from the product at checkout, so later price changes
    # don't alter what the customer paid.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField(
                                            validators = [
                                                validators.MinValueValidator(1) ,
                                                validators.MaxValueValidator(100)
                                                ])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product' , 'order'] , 
                                    name='unique_product_per_order'
                                    )]

    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price


    def __str__(self):
        return f'{self.quantity} x {self.product}'






