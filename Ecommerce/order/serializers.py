from rest_framework import serializers
from django.conf import settings
from . import models
from store.models import Product


class MiniProductSerializer(serializers.ModelSerializer):
    """Just enough product info to show inside an order."""

    class Meta:
        model = Product
        fields = ['id','name_en']


class OrderItemSerializer(serializers.ModelSerializer):
    """Read-only: order items are only created by checkout."""
    
    product = MiniProductSerializer(read_only=True)

    class Meta:
        model = models.OrderItem
        fields = ['product','unit_price','quantity','total_price']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Read-only view of an order with its items and total."""

    order_items = OrderItemSerializer(many=True , read_only=True)
    
    class Meta:
        model = models.Order
        fields = ['id','status','created_at','order_items','total_price']
        read_only_fields = fields

        
    