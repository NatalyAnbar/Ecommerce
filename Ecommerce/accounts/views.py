from rest_framework import generics, mixins, permissions
from rest_framework.viewsets import GenericViewSet
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from . import models,Serializers

class RegisterUser(mixins.CreateModelMixin , GenericViewSet):
    """
    Sign up: POST /accounts/register/ with email and password.

    Only creating is allowed, so the endpoint can't be used to list,
    read or change other users.
    """
    
    queryset = models.User.objects.all()
    serializer_class = Serializers.RegisterSerializer
    # Visitors sign up before they have an account, so this must stay open
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """
    The logged-in user's profile: GET to read it, PUT or PATCH to update the name.

    There is no id in the URL; the user always comes from the token,
    so nobody can reach another user's profile.
    """
    
    serializer_class = Serializers.MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = Serializers.ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['put','head','options']

    def get_object(self):
        return self.request.user


class LoginView(TokenObtainPairView):
    """Log in with email and password; limited to stop password guessing."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'