from rest_framework import serializers
from . import models
from store.Serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):

    # Include full product details inside each shopping cart item
    pro = ProductSerializer(read_only=True)

    class Meta:
        model = models.CartItem
        fields = ['product','quantity','pro','total_price']


class AddItemSerializer(serializers.ModelSerializer):

    # Handle incoming user input to add or update items in the cart
    class Meta:
        model = models.CartItem
        fields = ['product','quantity']


class CartSerializer(serializers.ModelSerializer):

    # Represent the main user cart with all nested items
    cart_items = CartItemSerializer(many=True,read_only=True)
    
    class Meta:
        model = models.Cart
        fields = ['id','user','cart_items','total_price']


