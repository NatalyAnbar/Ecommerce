from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()

router.register('categories',views.CategoryView,basename='category')
router.register('products',views.ProductView,basename='product')

# Endpoints that belong to a single product: /products/<slug>/reviews/ and /products/<slug>/images/
products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('reviews', views.ReviewView, basename='product_review')
products_router.register('images', views.ProductImageView, basename='product-images')

urlpatterns = [
    path('',include(router.urls)),
    path('',include(products_router.urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)