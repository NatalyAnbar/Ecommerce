from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()

router.register('categories',views.CategoryView,basename='category')
router.register('products',views.ProductView,basename='product')
router.register('images',views.ProductImageView,basename='image')

urlpatterns = [
    path('',include(router.urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)