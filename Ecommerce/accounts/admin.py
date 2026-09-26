from django.contrib import admin
from .models import User

# Register custom user model to manage users inside Django Admin panel
admin.site.register(User)