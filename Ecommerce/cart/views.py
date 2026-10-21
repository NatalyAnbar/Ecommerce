from rest_framework.viewsets import ModelViewSet
from django.db import transaction
from . import models,Serializers
from rest_framework import permissions,status,generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action


class CartView(ModelViewSet):
    serializer_class = Serializers.CartSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Context split based on user authentication status
        user = self.request.user
        if user.is_authenticated:
            return models.Cart.objects.prefetch_related('cart_items').filter(user=user)
        if self.action == 'list':
            return models.Cart.objects.none()
        return models.Cart.objects.prefetch_related('cart_items').filter(user=None)


    def perform_create(self, serializer):
        # Custom create to inject active user inside the cart
        user = self.request.user
        if user.is_authenticated:
            if models.Cart.objects.filter(user=user).exists():
                raise ValidationError({"detail": "Cart already exists for this user."})
            serializer.save(user=user)
        else:
            serializer.save()


    @action(detail=True , methods=['delete'])
    def clear(self, request, pk=None):
        """Empty the cart but keep it: DELETE /carts/<id>/clear/."""
        # get_object applies the same rule as everywhere else: your cart, or an anonymous one
        cart = self.get_object()
        cart.cart_items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemView(ModelViewSet):

    serializer_class = Serializers.CartItemSerializer
    # Carts work without logging in; the queryset decides whose cart you can reach
    permission_classes = [permissions.AllowAny]
    # PUT would require product_id on every edit; quantity changes use PATCH
    http_method_names = ['post','get','patch','delete','head','options']

    def get_cart(self):
        """The cart from the URL, if this request may use it; otherwise a 404."""
        user = self.request.user
        # Logged in: only your own cart. Not logged in: only anonymous carts.
        owner = user if user.is_authenticated else None
        return get_object_or_404(models.Cart, pk=self.kwargs['cart_pk'], user=owner)

    def get_queryset(self):
        # Checking the cart first turns someone else's cart into a 404, not an empty list
        cart = self.get_cart()
        return models.CartItem.objects.select_related('product').filter(cart=cart)

    
    def perform_create(self, serializer):
        # Same rule as get_queryset: you can only add to your own (or an anonymous) cart
        self.get_cart()
        serializer.save()


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['cart_id'] = self.kwargs['cart_pk']
        return context


class MergeCartView(generics.GenericAPIView):
    """
    Move an anonymous cart into the logged-in user's cart: POST /carts/merge/.
    Called after login. Products in both carts are added up (capped at 100),
    and the anonymous cart is deleted.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Serializers.MergeCartSerializer

    def post(self,request):
        # Rejects a missing or malformed id with a 400 instead of crashing the lookup
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        guest_id = serializer.validated_data['cart_id']
        guest_cart = get_object_or_404(models.Cart, id=guest_id, user=None)

        user_cart , _ = models.Cart.objects.get_or_create(user=request.user)
        items = guest_cart.cart_items.select_related('product')

        # All of it or none of it: a failure halfway must not leave the items half-moved
        with transaction.atomic():
            for item in items:
                new_item,created = models.CartItem.objects.get_or_create(
                    cart = user_cart,
                    product = item.product,
                    defaults={'quantity': item.quantity}
                )
                if not created :
                    # Same product in both carts: one line with the quantities added up
                    new_item.quantity = min(new_item.quantity + item.quantity , 100)
                    new_item.save(update_fields=['quantity'])

            guest_cart.delete()

        return Response({
            'message': 'Cart merged successfully', 
            'cart': Serializers.CartSerializer(user_cart, context={'request': request}).data
        })



        

        
        