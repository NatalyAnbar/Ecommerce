from django.db import models
from accounts.models import User
from store.models import Product
from django.core.validators import MaxValueValidator
import uuid

class Cart(models.Model):

    # Secure token ID instead of sequential integers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(User,on_delete=models.CASCADE,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    @property
    def totalPrice(self):
        # Calculate subtotal price for all cart items
        items = self.cart_items.all()
        total = sum([item.quantity * item.product.price for item in items])
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='cart_items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product_cart_items')
    quantity = models.PositiveIntegerField(default=1,validators=[MaxValueValidator(100)])

    @property
    def total_price(self):
        # Calculate subtotal price for this single item 
        return self.product.price * self.quantity

    def __str__(self):
        return str(self.id)

    class Meta:
        # Enforce safety constraints to prevent duplicate product lines inside one cart
        constraints = [
            models.UniqueConstraint(fields=['cart','product'], name='unique_cart_product')
        ]



