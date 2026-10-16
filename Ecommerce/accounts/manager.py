
"""Creates users that log in with an email instead of a username."""

from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Shared steps for every kind of user: check, normalise, hash, save."""
        if not email:
            raise ValueError('Users must have an email address.')

        # Lowercase the domain
        email = self.normalize_email(email)
        user = self.model(email=email , **extra_fields)

        # Stores a hash, never the plain password
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_user(self, email, password=None, **extra_fields):
        """Create a regular user; staff access can be granted, superuser access can't."""
        extra_fields.setdefault('is_staff',False)
        extra_fields.setdefault('is_superuser',False)

        if extra_fields['is_superuser'] :
            raise ValueError('Use create_superuser to create a superuser.')
        
        return self._create_user(email,password,**extra_fields)


    def create_superuser(self, email, password=None, **extra_fields):
        """Create a user with full admin access."""
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)

        # A superuser without these flags couldn't open the admin, which is always a mistake
        if not extra_fields['is_staff'] or not extra_fields['is_superuser']:
            raise ValueError('A superuser must have is_staff and is_superuser set to True.')
        
        return self._create_user(email,password,**extra_fields)