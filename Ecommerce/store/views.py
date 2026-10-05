from rest_framework.viewsets import ModelViewSet
from . import models,Serializers,filters
from django.db.models import Avg,Count
from rest_framework import permissions


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
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

    # Partial, case-insensitive match in either language
    search_fields = ['name_en','name_ar']


class ProductView(ModelViewSet):
    """
    CRUD endpoints for products, looked up by slug.
    Anyone can read; writes require the matching Django model permission.
    Supports filtering, search, and pagination:
    `?category=phones&price_min=100&price_max=500&search=apple&page_size=5`&ordering=-price
    """

    queryset = (
        models.Product.objects
        # Load gallery images in one extra query instead of one per product
        .prefetch_related('images','product_reviews')
        # Average rating and review count are computed per request, so they never go stale
        .annotate(
            avg_rating=Avg('product_reviews__rating'),
            reviews_count=Count('product_reviews'),
        )
    )
    serializer_class = Serializers.ProductSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

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
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]


class ReviewView(ModelViewSet):
    """
    Reviews nested under a product: /products/<slug>/reviews/.

    Anyone can read; authenticated users can post one review per product
    and only edit or delete their own.
    """

    serializer_class = Serializers.ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_slug = self.kwargs['product_slug']
        product = models.Product.objects.filter(id=product_slug)
        return models.Review.objects.filter(user=self.request.user , product=product)


    def get_serializer_context(self):
        # Pass the product from the URL so the serializer can enforce one review per user
        context = super().get_serializer_context()
        context['product_slug'] = self.kwargs['product_slug']
        return context
    

    def perform_create(self, serializer):
        # Author and product come from the request and URL, never from the client payload
        user = self.request.user
        product_pk = self.kwargs['product_slug']
        product = models.Product.objects.get_object_or_404(id=product_pk)
        serializer.save(user=user,product=product)