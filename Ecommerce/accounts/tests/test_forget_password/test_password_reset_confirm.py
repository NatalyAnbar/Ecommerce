import re
from urllib.parse import parse_qs, urlparse

import pytest
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts import emails, models
from .conftest import OLD_PASSWORD

pytestmark = pytest.mark.django_db

NEW_PASSWORD = 'N3w-strong-pass!'


def get_url():
    return reverse('password_reset_confirm')


def params_from_link(link):
    """The uid and token from a reset link, as a frontend would read them."""
    query = parse_qs(urlparse(link).query)
    return {'uid': query['uid'][0], 'token': query['token'][0]}


def make_data(account, **extra_fields):
    """A valid confirm payload for account, built from a real reset link."""
    return {
        **params_from_link(emails.build_password_reset_link(account)),
        'new_password': NEW_PASSWORD,
        'confirm_new_password': NEW_PASSWORD,
    } | extra_fields


def confirm(client, data):
    return client.post(get_url(), data, format='json')


def assert_password_unchanged(account):
    account.refresh_from_db()
    assert account.check_password(OLD_PASSWORD)


# --- Success ---

def test_valid_link_sets_the_new_password(api_client, user):
    response = confirm(api_client, make_data(user))

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert not user.check_password(OLD_PASSWORD)


def test_reset_link_works_only_once(api_client, user):
    data = make_data(user)

    first = confirm(api_client, data)
    second = confirm(api_client, data)

    assert first.status_code == 200
    assert second.status_code == 400


def test_reset_logs_out_every_device(api_client, user):
    # A device that logged in with the old password
    login = api_client.post(
        reverse('login'), {'email': user.email, 'password': OLD_PASSWORD}, format='json'
    )
    refresh = login.data['refresh']

    confirm(api_client, make_data(user))

    response = api_client.post(reverse('refresh'), {'refresh': refresh}, format='json')
    assert response.status_code == 401


# --- Invalid links: all 400 with the same message, never 500 ---

def test_forged_token_is_rejected(api_client, user):
    response = confirm(api_client, make_data(user, token='fake-token'))

    assert response.status_code == 400
    assert_password_unchanged(user)


def test_malformed_uid_is_rejected(api_client, user):
    response = confirm(api_client, make_data(user, uid='abc!!'))

    assert response.status_code == 400
    assert_password_unchanged(user)


def test_uid_of_missing_user_is_rejected(api_client, user):
    missing_uid = urlsafe_base64_encode(force_bytes(999999))

    response = confirm(api_client, make_data(user, uid=missing_uid))

    assert response.status_code == 400


def test_token_of_another_user_is_rejected(api_client, user):
    other = models.User.objects.create_user(email='other@gmail.com', password=OLD_PASSWORD)
    other_token = params_from_link(emails.build_password_reset_link(other))['token']

    response = confirm(api_client, make_data(user, token=other_token))

    assert response.status_code == 400
    assert_password_unchanged(user)


def test_expired_token_is_rejected(api_client, user, settings):
    data = make_data(user)
    # Every link is already older than the allowed age
    settings.PASSWORD_RESET_TIMEOUT = -1

    response = confirm(api_client, data)

    assert response.status_code == 400
    assert_password_unchanged(user)


# --- Invalid passwords: the old one stays ---

def test_mismatched_passwords_are_rejected(api_client, user):
    response = confirm(api_client, make_data(user, confirm_new_password='Other-pass-99'))

    assert response.status_code == 400
    assert 'confirm_new_password' in response.data
    assert_password_unchanged(user)


def test_weak_password_is_rejected(api_client, user):
    response = confirm(
        api_client, make_data(user, new_password='123', confirm_new_password='123')
    )

    assert response.status_code == 400
    assert 'new_password' in response.data
    assert_password_unchanged(user)


def test_new_password_is_never_returned(api_client, user):
    response = confirm(api_client, make_data(user))

    assert NEW_PASSWORD not in str(response.data)


# --- The whole story ---

def test_full_reset_flow_from_email_to_login(api_client, user):
    api_client.post(reverse('password_reset'), {'email': user.email}, format='json')

    # Read the link from the email, as the user would
    link = re.search(r'https?://\S+', mail.outbox[0].body).group()
    data = {
        **params_from_link(link),
        'new_password': NEW_PASSWORD,
        'confirm_new_password': NEW_PASSWORD,
    }
    assert confirm(api_client, data).status_code == 200

    login = api_client.post(
        reverse('login'), {'email': user.email, 'password': NEW_PASSWORD}, format='json'
    )
    assert login.status_code == 200