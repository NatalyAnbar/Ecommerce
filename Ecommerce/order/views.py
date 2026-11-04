from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import permissions , status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.response import Response
from . import serializers , models
from cart.models import Cart
from payment.serializers import PaySerializer, PaymentSerializer
from payment.gateway import charge_card
from payment.models import Payment



class OrderView(ReadOnlyModelViewSet):
    """List and show the signed-in user's own orders."""

    serializer_class = serializers.OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        
        # Swagger builds the docs with a fake request; give it an empty queryset.
        if getattr(self, 'swagger_fake_view', False):
            return models.Order.objects.none()
        
        return models.Order.objects.filter(user=self.request.user).prefetch_related('order_items__product')


    @extend_schema(
        summary='Create an order from the cart',
        request=None,
        responses={
            201: serializers.OrderSerializer,
            400: OpenApiResponse(description='Cart is empty or not enough stock.'),
        },
    )
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


    @extend_schema(
        summary='Cancel a pending order',
        request=None,
        responses={
            200: serializers.OrderSerializer,
            400: OpenApiResponse(description='Only pending orders can be cancelled.'),
            404: OpenApiResponse(description='Order not found.'),
        },
    )
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


    @extend_schema(
        summary='Pay for a pending order',
        request=PaySerializer,
        responses={
            201: PaymentSerializer,
            400: OpenApiResponse(description='Invalid card number, or the order is not pending.'),
            402: PaymentSerializer,
            404: OpenApiResponse(description='Order not found.'),
        },
    )
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Pay for a pending order with a card, through the simulated gateway."""
        
        serializer = PaySerializer(data=request.data, context={'order_pk': pk})
        serializer.is_valid(raise_exception=True)
        card_number = serializer.validated_data['card_number']
        
        # All or nothing: a recorded payment and the order's status always agree
        with transaction.atomic():
            # Lock the order so two payments for it can't run at the same time
            order = get_object_or_404(
                models.Order.objects.select_for_update(),
                pk=pk,
                user=request.user,
            )
        
            # Checked after the lock
            if order.status != models.Order.Status.PENDING:
                return Response(
                    {'detail': 'Only pending orders can be paid.'},
                    status=status.HTTP_400_BAD_REQUEST,
                    )
        
            payment_status = charge_card(card_number)
        
            # Every attempt is recorded, declined ones included
            payment = Payment.objects.create(
                order=order,
                amount=order.total_price,
                status=payment_status,
                # The full card number is never stored
                card_last4=card_number[-4:],
                )
        
            if payment_status == Payment.Status.SUCCEEDED:
                order.status = models.Order.Status.PAID
                order.save(update_fields=['status'])
        
        response_status = (
            status.HTTP_201_CREATED
            if payment_status == Payment.Status.SUCCEEDED
            # 402 Payment Required: the card was declined, the order is still unpaid
            else status.HTTP_402_PAYMENT_REQUIRED
            )
        return Response(PaymentSerializer(payment).data, status=response_status)

                

