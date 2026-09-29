import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    def do_permission(*permissions):
        user = baker.make(User)
        for per in permissions:
            permission = Permission.objects.get(codename=per)
            user.user_permissions.add(permission)
        api_client.force_authenticate(user=user)
    return do_permission