from rest_framework.viewsets import ModelViewSet
from . import models,Serializers
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly


class CategoryView(ModelViewSet):
    """
    CRUD endpoints for categories, looked up by slug.
    Anyone can read; writes require the matching Django model permission.
    """

    # Prefetch products and their images to avoid N+1 queries in the nested serializers
    queryset = models.Category.objects.prefetch_related('products__images').all()
    serializer_class = Serializers.CategorySerializer
    lookup_field = 'slug'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class ProductView(ModelViewSet):
    """
    CRUD endpoints for products, looked up by slug.
    Anyone can read; writes require the matching Django model permission.
    """

    # Prefetch gallery images to avoid one query per product
    queryset = models.Product.objects.prefetch_related('images').all()
    serializer_class = Serializers.ProductSerializer
    lookup_field = 'slug'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class ProductImageView(ModelViewSet):
    """
    CRUD endpoints for product gallery images, looked up by id.
    Anyone can read; writes require the matching Django model permission.
    """

    # The serializer exposes only the product id, so no related data needs to be fetched
    queryset = models.ProductImage.objects.all()
    serializer_class = Serializers.ImageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]