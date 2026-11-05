import pytest
from accounts import models

OLD_PASSWORD = 'Old-pass-123'


@pytest.fixture
def user():
    """A user with a known, properly hashed password."""
    return models.User.objects.create_user(email='test@gmail.com', password=OLD_PASSWORD)