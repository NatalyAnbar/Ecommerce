from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView


rouetr = DefaultRouter()
rouetr.register('register',views.RegisterUser,basename='register')

urlpatterns = [
    path('',include(rouetr.urls)),


    path('login/',TokenObtainPairView.as_view(),name='login'),
    path('refreshtoken/',TokenRefreshView.as_view(),name='refresh'),
    path('logout/',TokenBlacklistView.as_view(),name='logout'),


    # A single URL with no id: the user comes from the token
    path('me/',views.MeView.as_view(),name='me'),
    path('change_password/',views.ChangePasswordView.as_view(),name='change_password')
]