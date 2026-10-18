from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager

class User(AbstractUser):
    """
    The store's user, identified by email instead of a username.

    Kept as a custom model from the start, so fields can be added later
    without a painful migration of Django's built-in user.
    """

    username = None

    # Each account needs its own email for password resets and order receipts
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    # Asked by createsuperuser besides the login field and password; nothing else is required
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


