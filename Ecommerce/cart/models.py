
"""Shopping carts: one per logged-in user, or an anonymous one identified by its id."""

from django.db import models
from accounts.models import User
from store.models import Product
from django.core.validators import MaxValueValidator,MinValueValidator
from decimal import Decimal
import uuid

class Cart(models.Model):
    """A list of products someone intends to buy, priced at the products' current prices."""

    # Secure token ID instead of sequential integers, so an anonymous cart's id can't be guessed
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Empty for anonymous carts; set once the cart belongs to a logged-in user
    user = models.OneToOneField(User,on_delete=models.CASCADE,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    @property
    def total_price(self) -> Decimal:
        """Sum of every line, recalculated on each read; prefetch items in the view."""
        items = self.cart_items.all()
        return sum(item.total_price for item in items)

    def clear_cart(self):
        """Remove every item from the cart."""
        return self.cart_items.all().delete()
    

class CartItem(models.Model):
    """One product in a cart and how many of it."""

    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='cart_items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product_cart_items')
    quantity = models.PositiveIntegerField(default=1,
                                           validators=[
                                               MinValueValidator(1),MaxValueValidator(100)
                                               ])

    class Meta:
        # Adding a product that's already in the cart raises the quantity instead of a new line
        constraints = [
            models.UniqueConstraint(fields=['cart','product'], name='unique_cart_product')
        ]

    def __str__(self):
        return f'{self.quantity} × {self.product}'

    @property
    def total_price(self) -> Decimal:
        """Price of this line at the product's current price."""
        return self.product.price * self.quantity










