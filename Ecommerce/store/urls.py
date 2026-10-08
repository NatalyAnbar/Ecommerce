from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()

router.register('categories',views.CategoryView,basename='category')
router.register('products',views.ProductView,basename='product')
router.register('images',views.ProductImageView,basename='image')
router.register('reviews',views.ReviewView,basename='review')

# Reviews live under their product: /products/<slug>/reviews/
nested_product_review = routers.NestedDefaultRouter(
    router,
    'products',
    lookup = 'product'
)

nested_product_review.register('reviews',views.ReviewView,basename='product_review')

urlpatterns = [
    path('',include(router.urls)),
    path('',include(nested_product_review.urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)