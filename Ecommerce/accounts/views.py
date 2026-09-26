from django.shortcuts import render
from rest_framework.viewsets import mixins,GenericViewSet
from . import models,Serializers

class RegisterUser(GenericViewSet,mixins.CreateModelMixin):
    # viewset optimized exclusively for handling new user registrations
    
    queryset = models.User.objects.all()
    serializer_class = Serializers.UserSerializer