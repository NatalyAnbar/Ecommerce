"""Emails sent to users about their account."""

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


def build_password_reset_link(user):
    """Return the link a user follows to choose a new password."""

    # The user's id, written so it fits in a URL; it isn't secret
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # Signed with SECRET_KEY, expires after PASSWORD_RESET_TIMEOUT,
    # and stops working once the password changes
    token = default_token_generator.make_token(user)
    return f'{settings.PASSWORD_RESET_URL}?uid={uid}&token={token}'


def send_password_reset_email(user):
    """Email the user a link to reset their password."""
    link = build_password_reset_link(user)
    send_mail(
        subject = 'Reset your password',
        message = (
            'We received a request to reset your password.\n\n'
            f'Choose a new one here: {link}\n\n'
            'The link works once and expires in one hour. '
            'If you did not ask for this, you can ignore this email.'
        ),
        from_email = None,
        recipient_list = [user.email]
    )


def decode_uid(uid):
    """Turn the uid from a reset link back into the user's primary key."""
    return force_str(urlsafe_base64_decode(uid))