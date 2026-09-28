from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
rouetr = DefaultRouter()
rouetr.register('register',views.RegisterUser)

urlpatterns = [
    path('',include(rouetr.urls)),
    path('login/',TokenObtainPairView.as_view()),
    path('refreshtoken/',TokenRefreshView.as_view())
]