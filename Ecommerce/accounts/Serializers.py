from rest_framework import serializers
from . import models

class UserSerializer(serializers.ModelSerializer):

    # Hide passwords from outgoing API responses for security

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)


    class Meta:
        model = models.User
        fields = ['id','username','email','password','confirm_password']

    def validate_password(self,value):
        # Check password strength limitation rule

        if len(value) < 8:
            raise serializers.ValidationError('The password must be longer than 8 characters.')
        return value


    def validate(self,attrs):
        # Secure safety match check between both password fields

        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('The passwords do not match')
        return attrs
    

    def create(self, validated_data):
        # Remove confirmation token and create a secure hashed user instance

        validated_data.pop('confirm_password')
        user = models.User.objects.create_user(**validated_data)
        return user