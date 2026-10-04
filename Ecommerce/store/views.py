from rest_framework.viewsets import ModelViewSet
from . import models,Serializers,filters,pagination
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly


class CategoryView(ModelViewSet):
    """
    CRUD endpoints for categories, looked up by slug.
    Anyone can read; writes require the matching Django model permission.
    Supports text search across both translations: `?search=electronics`.
    """

    # Prefetch products and their images to avoid N+1 queries in the nested serializers
    queryset = models.Category.objects.prefetch_related('products__images').all()
    serializer_class = Serializers.CategorySerializer
    lookup_field = 'slug'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    # Partial, case-insensitive match in either language
    search_fields = ['name_en','name_ar']


class ProductView(ModelViewSet):
    """
    CRUD endpoints for products, looked up by slug.
    Anyone can read; writes require the matching Django model permission.
    Supports filtering, search, and pagination:
    `?category=phones&price_min=100&price_max=500&search=apple&page_size=5`&ordering=-price
    """

    # Prefetch gallery images to avoid one query per product
    queryset = models.Product.objects.prefetch_related('images').all()
    serializer_class = Serializers.ProductSerializer
    lookup_field = 'slug'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    # Structured filters: category slug, brand, and price range
    filterset_class = filters.ProductFilter

    # Free-text search across names in both languages and the brand
    search_fields = ['name_en','name_ar','brand']

    ordering_fields = ['price']


class ProductImageView(ModelViewSet):
    """
    CRUD endpoints for product gallery images, looked up by id.
    Anyone can read; writes require the matching Django model permission.
    """

    # The serializer exposes only the product id, so no related data needs to be fetched
    queryset = models.ProductImage.objects.all()
    serializer_class = Serializers.ImageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]