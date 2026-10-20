
"""Serializers for the cart and its items."""

from rest_framework import serializers
from . import models
from store.models import Product
from store.Serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    """
    One line of a cart.

    Responses show the full product; requests send its id and quantity(1 by default). 
    Adding a product that's already in the cart raises that line's quantity instead of adding a line.
    """

    # Shown in responses: the whole product, read from the saved line
    product = ProductSerializer(read_only=True)
    # Sent when adding: only the id, checked in validate_product_id
    product_id = serializers.IntegerField(write_only = True)

    class Meta:
        model = models.CartItem
        fields = ['id','product_id','product','quantity','total_price']

    def validate_product_id(self , value):
        """The product must exist, and an existing line can't switch to another product."""

        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError('This product does not exist.') 

        # Editing a line changes its quantity only; a different product is a new line
        if self.instance and self.instance.product_id != value:
            raise serializers.ValidationError('The product of a cart line cannot be changed.')
        
        return value
    

    def validate(self , attrs):
        """Keep an item at 100 or fewer, counting what's already in the cart when adding."""

        # Only adding can push a line over the limit, because it adds to the existing
        # quantity; editing sets a new quantity, which the model's validator already caps
        if self.instance is None:
            product_id = attrs['product_id']
            cart_id = self.context['cart_id']

            if item := models.CartItem.objects.filter(
                product_id=product_id,cart_id=cart_id
                ).first():
                    total_quantity = attrs.get('quantity',1) + item.quantity
                    
                    if total_quantity > 100:
                        raise serializers.ValidationError(
                            {'quantity': 'A cart line cannot have more than 100 of a product.'}
                        )
        return attrs


    def create(self, validated_data):
        """Add a product to the cart; if it's already there, add to its quantity instead."""
        cart_id = self.context['cart_id']
        product_id = validated_data['product_id']
        quantity = validated_data.get('quantity',1)

        if item := models.CartItem.objects.filter(
            cart__id=cart_id,product__id=product_id
            ).first():
            # Same product again: one line with a bigger quantity, not a second line
            item.quantity += quantity
            item.save(update_fields=['quantity'])
        else:
            # The cart comes from the URL, so it's set here, not sent by the client
            item = models.CartItem.objects.create(
                cart_id=cart_id , product_id=product_id , quantity=quantity
             )
        return item


class CartSerializer(serializers.ModelSerializer):
    """A whole cart: its items and the total at current prices."""

    cart_items = CartItemSerializer(many=True , read_only=True)
    
    class Meta:
        model = models.Cart
        fields = ['id','cart_items','total_price','created_at','updated_at']


class MergeCartSerializer(serializers.Serializer):
    """The anonymous cart to merge into the logged-in user's cart."""
    
    cart_id = serializers.UUIDField()