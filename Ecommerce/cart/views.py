from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from . import models,Serializers
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

class CartView(ModelViewSet):
    serializer_class = Serializers.CartSerializer
    permission_classes = [AllowAny]

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


class CartItemView(ModelViewSet):
    serializer_class = Serializers.CartItemSerializer

    def get_queryset(self):
        # get cart items for only filtered cart

        pk = self.kwargs['cart_pk']

        if pk:
            return models.CartItem.objects.select_related('product_cart_items').filter(cart_id=pk)
            
        return models.CartItem.objects.select_related('product_cart_items').all()


    def perform_create(self, serializer):
        # Target specific cart nested route parent ID before adding an item

        pk = self.kwargs['cart_pk']
        try:
            cart = models.Cart.objects.get(cart_id=pk)
        except models.Cart.DoesNotExist:
            return Response('Cart does not exsist')
        serializer.save(cart=cart)


class AddItemView(ModelViewSet):
    queryset = models.CartItem.objects.all()
    serializer_class = Serializers.AddItemSerializer


class MergeCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        # Merge visitor guest cart data with authorized user profile

        visitor_id = self.request.data.get('cart_id')

        try:
            visitor_cart = models.Cart.objects.get(id=visitor_id,user=None)
        except models.Cart.DoesNotExist:
            return Response({'msg' : 'Cart already merged'})
        
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
                new_item.quantity += item.quantity
                new_item.save()

        # Flush temporary guest cart after successful data migration
        visitor_cart.delete()

        return Response({
            'message': 'Cart merged successfully', 
            'cart': Serializers.CartSerializer(user_cart, context={'request': request}).data
        })



        

        
        