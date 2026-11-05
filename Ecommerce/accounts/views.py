from rest_framework import generics, mixins, permissions, status
from rest_framework.viewsets import GenericViewSet
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from . import emails, models,Serializers
from django.db import transaction

class RegisterUser(mixins.CreateModelMixin , GenericViewSet):
    """
    Sign up: POST /accounts/register/ with email and password.

    Only creating is allowed, so the endpoint can't be used to list,
    read or change other users.
    """
    
    serializer_class = Serializers.RegisterSerializer
    # Visitors sign up before they have an account, so this must stay open
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """Log in with email and password; limited to stop password guessing."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


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


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Forgotten password: POST /accounts/password-reset/ with an email.

    Always answers the same way, so nobody can learn which emails have an account.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = Serializers.PasswordResetRequestSerializer
    # Limits how often anyone can trigger reset emails
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = models.User.objects.get(email__iexact=email)
        except models.User.DoesNotExist:
            # Unknown email: send nothing, and answer exactly as for a real one
            pass
        else:
            # Outside the try, so a failure to send the email isn't hidden
            emails.send_password_reset_email(user)

        return Response(
            {'detail': 'If an account exists for this email, a reset link has been sent.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(generics.GenericAPIView):
    """
    Set a new password: POST /accounts/password-reset/confirm/
    with uid, token and the new password typed twice.

    Logs the user out of every device by blacklisting their refresh tokens.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = Serializers.PasswordResetConfirmSerializer

    # Slows down anyone guessing tokens
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = Serializers.PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        user_id = emails.decode_uid(uid)
        new_password = serializer.validated_data['new_password']
        user = models.User.objects.get(id=user_id)

        # The new password and the logout happen together, or not at all
        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=['password'])

            # Sessions opened with the old password must not stay open on other devices
            for token in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=token)

        return Response(
            {'detail': 'Your password has been reset.'},
            status=status.HTTP_200_OK,
        )


        
        


