from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from . import models,Serializers
from rest_framework import permissions,status
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


class MergeCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self,request):
        serializer = Serializers.MergeCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Merge visitor guest cart data with authorized user profile
        visitor_id = serializer.validated_data['cart_id']
        visitor_cart = get_object_or_404(models.Cart, id=visitor_id, user=None)
        
        user = self.request.user
        user_cart,created = models.Cart.objects.get_or_create(user=user)
        items = visitor_cart.cart_items.all()

        # Sequentially append or update item quantities 
        for item in items:
            new_item,created = models.CartItem.objects.get_or_create(
                cart = user_cart,
                product = item.product,
                defaults={'quantity': item.quantity}
            )
            if not created :
                new_item.quantity = min(new_item.quantity + item.quantity , 100)
                new_item.save(update_fields=['quantity'])

        # Flush temporary guest cart after successful data migration
        visitor_cart.delete()

        return Response({
            'message': 'Cart merged successfully', 
            'cart': Serializers.CartSerializer(user_cart, context={'request': request}).data
        })



        

        
        