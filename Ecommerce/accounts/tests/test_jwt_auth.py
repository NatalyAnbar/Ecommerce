
"""Tests for JWT login, refresh-token rotation and logout."""

import pytest
from django.urls import reverse

from accounts import models

pytestmark = pytest.mark.django_db

EMAIL = 'test123@gmail.com'
PASSWORD = 'blabla@123'


# ---------- fixtures ----------

@pytest.fixture
def user():
    # create_user hashes the password, so login can check it.
    return models.User.objects.create_user(
        email=EMAIL,
        first_name='test_nat',
        last_name='test_anb',
        password=PASSWORD,
    )


@pytest.fixture
def tokens(api_client, user):
    """Log in and return {'access': ..., 'refresh': ...}."""
    return login(api_client, PASSWORD).data


# ---------- helpers ----------

def login(api_client, password):
    return api_client.post(
        reverse('login'),
        {'email': EMAIL, 'password': password},
        format='json',
    )


def refresh(api_client, refresh_token):
    return api_client.post(
        reverse('refresh'),
        {'refresh': refresh_token},
        format='json',
    )


def logout(api_client, refresh_token):
    return api_client.post(
        reverse('logout'),
        {'refresh': refresh_token},
        format='json',
    )


# ---------- login ----------

def test_login_with_correct_credentials_returns_tokens(api_client, user):
    response = login(api_client, PASSWORD)

    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data


def test_login_with_wrong_password_returns_401(api_client, user):
    response = login(api_client, '1234@test')

    assert response.status_code == 401


# ---------- refresh rotation ----------

def test_refresh_returns_a_new_refresh_token(api_client, tokens):
    response = refresh(api_client, tokens['refresh'])

    assert response.status_code == 200
    assert 'access' in response.data
    # Rotation: a brand-new refresh token, not the old one.
    assert response.data['refresh'] != tokens['refresh']


def test_old_refresh_token_is_rejected_after_rotation(api_client, tokens):
    refresh(api_client, tokens['refresh'])

    # The first refresh blacklisted the old token, so it can't be reused.
    response = refresh(api_client, tokens['refresh'])

    assert response.status_code == 401


def test_new_refresh_token_keeps_working(api_client, tokens):
    new_refresh = refresh(api_client, tokens['refresh']).data['refresh']

    response = refresh(api_client, new_refresh)

    assert response.status_code == 200


# ---------- logout ----------

def test_logout_blacklists_the_refresh_token(api_client, tokens):
    logout_response = logout(api_client, tokens['refresh'])
    refresh_response = refresh(api_client, tokens['refresh'])

    assert logout_response.status_code == 200
    assert refresh_response.status_code == 401


def test_logout_with_invalid_token_returns_401(api_client):
    # The token is there but isn't a real one.
    response = logout(api_client, 'not-a-real-token')

    assert response.status_code == 401


def test_logout_without_token_returns_400(api_client):
    # The refresh field is missing altogether.
    response = api_client.post(reverse('logout'), {}, format='json')

    assert response.status_code == 400