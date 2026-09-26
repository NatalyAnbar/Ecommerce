from django.urls import path,include
from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register('carts',views.CartView,basename='cart')
router.register('additems',views.AddItemView)


# Setup hierarchical nested routes structure for tracking cart rows
cart_items_nested_router = routers.NestedDefaultRouter(
    router,
    'carts',
    lookup = 'cart'
)

cart_items_nested_router.register(
    'cartitems'
    ,views.CartItemView,
    basename='cartitems'
    )

urlpatterns = [
    path('',include(router.urls)),
    path('',include(cart_items_nested_router.urls)),
    path('mergeCart/',views.MergeCartView.as_view())
]