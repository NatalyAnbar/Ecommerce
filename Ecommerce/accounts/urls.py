from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


rouetr = DefaultRouter()
rouetr.register('register',views.RegisterUser,basename='register')

urlpatterns = [
    path('',include(rouetr.urls)),
    path('login/',TokenObtainPairView.as_view()),
    path('refreshtoken/',TokenRefreshView.as_view()),
    # A single URL with no id: the user comes from the token
    path('me/',views.MeView.as_view(),name='me'),
    path('change_password/',views.ChangePasswordView.as_view(),name='change_password')
]