from rest_framework.viewsets import ModelViewSet
from . import models,Serializers,filters,store_permissions
from django.db.models import Avg,Count
from rest_framework import permissions
from django.shortcuts import get_object_or_404


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
        .prefetch_related('images')
        # Average rating and review count are computed per request, so they never go stale
        .annotate(
            avg_rating=Avg('product_reviews__rating'),
            reviews_count=Count('product_reviews'),
        )
        # Meta.ordering is ignored once annotate() groups rows, so order explicitly
        .order_by('slug')
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
    Gallery images nested under a product: /products/<slug>/images/.

    Images are added only through the product form; this endpoint lists,
    edits and deletes them. Anyone can read; writes require the matching
    Django model permission.

    No POST: new images are uploaded with the product.
    No PUT: it requires the file, so changing a title would mean re-uploading the image;
    PATCH covers every edit, including replacing the file.
    """

    http_method_names = ['get', 'patch', 'delete', 'head', 'options']
    serializer_class = Serializers.ImageSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        """Images of the product in the URL (empty if the product doesn't exist)."""
        product_slug = self.kwargs['product_slug']
        return models.ProductImage.objects.filter(product__slug=product_slug)


class ReviewView(ModelViewSet):
    """
    Reviews nested under a product: /products/<slug>/reviews/.

    Anyone can read; authenticated users can post one review per product
    and only edit or delete their own.
    """

    serializer_class = Serializers.ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,store_permissions.IsOwnerOrReadOnly]

    def get_product(self):
        """The product from the URL, fetched once per request (404 if it doesn't exist)."""
        product_slug = self.kwargs['product_slug']
        return get_object_or_404(models.Product , slug=product_slug)


    def get_queryset(self):
        return models.Review.objects.select_related('user').filter(product=self.get_product())


    def get_serializer_context(self):
        """ Pass the product from the URL so the serializer can enforce one review per user """
        context = super().get_serializer_context()
        context['product_slug'] = self.kwargs['product_slug']
        return context
    

    def perform_create(self, serializer):
        """ Author and product come from the request and URL, never from the client payload """
        user = self.request.user
        serializer.save(user=user,product=self.get_product())