from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers

from . import models


class RegisterSerializer(serializers.ModelSerializer):

    """Sign up with an email and a password typed twice."""

    # Passwords are only ever received, never sent back in responses
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})


    class Meta:
        model = models.User
        # Admin flags (is_staff, is_superuser) are left out, so a client can't grant them
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'confirm_password']


    def validate_email(self, value):
        """ One account per address, however it's capitalised """
        email = value.lower()
        # The built-in unique check runs before lowercasing, so check again in any case
        if models.User.objects.filter(email__iexact = email).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return email
    

    def validate(self,attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'The passwords do not match.'})

        # Django's password rules from settings: length, common passwords, digits only,
        # and similarity to the user's own details
        user = models.User(email=attrs['email'])
        try:
            validate_password(attrs['password'],user=user)
        except ValidationError as error:
            # Show Django's messages under the password field, not as a general error
            raise serializers.ValidationError({'password': list(error.messages)})
        return attrs
    

    def create(self, validated_data):
        """Create the user through create_user, which hashes the password."""
        validated_data.pop('confirm_password')
        return models.User.objects.create_user(**validated_data)


class MeSerializer(serializers.ModelSerializer):
    """The logged-in user's own profile."""

    class Meta:
        model = models.User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined']
        # Changing the email changes the login, so it needs its own verified flow
        read_only_fields = ['id', 'email','date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Change the logged-in user's password.

    Takes the current password and the new one twice. The view passes the
    user in as the instance, so saving calls update().
    """

    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        """Make sure the person changing the password knows the current one."""
        if not self.instance.check_password(value):
            raise serializers.ValidationError('The old password is incorrect.')
        return value


    def validate_new_password(self, value):
        """Run Django's password rules (length, common, numeric, similar to the user)."""
        try:
            # The user is passed so the password can't be too close to their email or name
            validate_password(value, user=self.instance)
        except ValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return value

    def validate(self, attrs):
        """Compare the two new passwords"""
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': 'The passwords do not match.'})
        return attrs


    def update(self, instance, validated_data):
        """Hash and store the new password"""
        instance.set_password(validated_data['new_password'])
        # Only the password column changes, so only that one is written
        instance.save(update_fields=['password'])
        return instance

    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Set a new password from a reset link.

    The uid and token come from the emailed link; the client sends them
    in the body together with the new password typed twice.
    """

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        # One message for every link problem, so nobody learns which part was wrong
        invalid_link = serializers.ValidationError('Invalid or expired link.')

        # The uid tells us whose link this is
        try:
            user_pk = force_str(urlsafe_base64_decode(attrs['uid']))
            user = models.User.objects.get(pk=user_pk)
        except (TypeError, ValueError, OverflowError, models.User.DoesNotExist):
            raise invalid_link

        # The token proves the link is genuine, unused and not expired.
        if not default_token_generator.check_token(user, attrs['token']):
            raise invalid_link

        # Both passwords match
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': 'The passwords do not match.'}
            )

        # Django's password rules, including similarity to this user's details
        try:
            validate_password(attrs['new_password'], user=user)
        except ValidationError as error:
            raise serializers.ValidationError({'new_password': list(error.messages)})

        return attrs
    

class GoogleLoginSerializer(serializers.Serializer):
    """Check a Google ID token and pass on the user's email and name."""
    
    id_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            # Checks Google's signature, expiry (exp), issuer (iss) and that
            # the token was issued for our app (aud)
            google_info = id_token.verify_oauth2_token(
                attrs['id_token'],
                google_requests.Request(),
                audience=settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            raise serializers.ValidationError({'id_token': 'Invalid Google token.'})

        if not google_info.get('email_verified'):
            raise serializers.ValidationError({'id_token': 'Google email is not verified.'})

        attrs['email'] = google_info['email']
        attrs['first_name'] = google_info.get('given_name','')
        attrs['last_name'] = google_info.get('family_name','')
        return attrs

