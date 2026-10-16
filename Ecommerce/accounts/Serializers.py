from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
        fields = ['email', 'first_name', 'last_name', 'date_joined']
        # Changing the email changes the login, so it needs its own verified flow
        read_only_fields = ['email','date_joined']
