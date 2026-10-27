from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import permissions , status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.response import Response
from . import serializers , models
from cart.models import Cart


class OrderView(ReadOnlyModelViewSet):
    """List and show the signed-in user's own orders."""

    serializer_class = serializers.OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return models.Order.objects.filter(user=self.request.user).prefetch_related('order_items__product')


    @action(detail=False , methods=['post'])
    def checkout(self, request):
        """Turn the user's cart into a pending order and empty the cart."""

        user_cart = Cart.objects.filter(user=request.user).first()

        if not user_cart or not user_cart.cart_items.exists():
            return Response(
                {'detail': 'Your cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        cart_items = user_cart.cart_items.select_related('product')

        # All or nothing: if anything fails, no half-made order is left behind.
        with transaction.atomic():
            order = models.Order.objects.create(user=request.user)
            for item in cart_items:
                models.OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    # Snapshot of today's price, so later changes don't affect this order.
                    unit_price=item.product.price
                )

            user_cart.clear_cart()

        return Response(serializers.OrderSerializer(order).data ,
                         status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel one of the user's pending orders."""

        # get_object uses get_queryset, so other users' orders give 404.
        order = self.get_object()

        if order.status != models.Order.Status.PENDING:
            return Response(
                {'detail': 'Only pending orders can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        order.status = models.Order.Status.CANCELLED
        order.save(update_fields=['status'])

        return Response(serializers.OrderSerializer(order).data)
