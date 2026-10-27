import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache

User = get_user_model()

@pytest.fixture
def api_client():
    """An API client with no user logged in."""
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    """
    Return a function that logs in a new user on `api_client`.

    Pass permission codenames to grant them.
    The created user is returned so tests can use it as an owner.
    """
    def do_permission(*permissions):
        user = baker.make(User)
        for per in permissions:
            permission = Permission.objects.get(codename=per)
            user.user_permissions.add(permission)
        api_client.force_authenticate(user=user)
        return user
    return do_permission


@pytest.fixture(autouse=True)
def temp_media_root(settings, tmp_path):
    """Save uploaded files to a temporary folder so tests don't fill the real media folder."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Rate limits count in the cache; reset them so each test starts fresh."""
    cache.clear()