from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import permissions , status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.response import Response
from . import serializers , models
from cart.models import Cart
from django.db.models import F


class OrderView(ReadOnlyModelViewSet):
    """List and show the signed-in user's own orders."""

    serializer_class = serializers.OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        
        # Swagger builds the docs with a fake request; give it an empty queryset.
        if getattr(self, 'swagger_fake_view', False):
            return models.Order.objects.none()
        
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

        # All or nothing: if anything fails, no half-made order is left behind.
        with transaction.atomic():

            # Hold these products until we finish, so no one else can buy the same last unit.
            cart_items = list(user_cart
                              .cart_items
                              .select_related('product')
                              .select_for_update(of=('product',)))

            # Check everything before writing anything.
            if unavailable := [
                item.product.name_en 
                for item in cart_items 
                if item.product.stock < item.quantity
                ]:
                return Response(
                                {'detail': 'Not enough stock.', 'products': unavailable},
                                status=status.HTTP_400_BAD_REQUEST,
                                )

            order = models.Order.objects.create(user=request.user)
            
            for item in cart_items:
                models.OrderItem.objects.create (
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    # Snapshot of today's price, so later changes don't affect this order.
                    unit_price=item.product.price
                        )
                
                models.Product.objects.filter(id=item.product.id).update(stock=F('stock')-item.quantity)

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

        with transaction.atomic():
            # The status and the stock change together, or not at all.
            for item in order.order_items.all():
                models.Product.objects.filter(id=item.product.id).update(stock=F('stock') + item.quantity)
            order.status = models.Order.Status.CANCELLED
            order.save(update_fields=['status'])

        return Response(serializers.OrderSerializer(order).data)
