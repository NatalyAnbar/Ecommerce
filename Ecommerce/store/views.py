from rest_framework.viewsets import ModelViewSet
from . import models,Serializers
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly


class CategoryView(ModelViewSet):

    # OPTIMIZED: Changed from slow N+1 queries to only 2 fast database queries
    queryset = models.Category.objects.prefetch_related('products').all()
    serializer_class = Serializers.CategorySerializer
    lookup_field = 'slug'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class ProductView(ModelViewSet):

    # OPTIMIZED: Changed from slow N+1 queries to only 2 fast database queries
    queryset = models.Product.objects.prefetch_related('images').all()
    serializer_class = Serializers.ProductSerializer
    lookup_field = 'slug'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class ProductImageView(ModelViewSet):

    # view and manage product gallery images
    queryset = models.ProductImage.objects.all()
    serializer_class = Serializers.ImageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]