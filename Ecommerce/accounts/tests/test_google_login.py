from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

pytestmark = pytest.mark.django_db

CLIENT_ID = 'test-client-id.apps.googleusercontent.com'

# Patched where the serializer looks it up, so no test ever calls Google
VERIFY_PATH = 'accounts.Serializers.id_token.verify_oauth2_token'


# --- Fixtures ---

@pytest.fixture(autouse=True)
def google_client_id(settings):
    """Give the tests a known client ID, whatever is in the real .env."""
    settings.GOOGLE_CLIENT_ID = CLIENT_ID


@pytest.fixture
def google_info():
    """What Google returns for a valid ID token."""
    return {
        'iss': 'https://accounts.google.com',
        'aud': CLIENT_ID,
        'email': 'salma@gmail.com',
        'email_verified': True,
        'given_name': 'Salma',
        'family_name': 'Haddad',
    }


@pytest.fixture
def mock_verify(google_info):
    """Replace Google's check with a fake that accepts the token."""
    with patch(VERIFY_PATH, return_value=google_info) as mocked:
        yield mocked


def google_login(api_client, token='fake-google-token'):
    return api_client.post(reverse('google_login'), {'id_token': token}, format='json')


# --- Success ---

def test_new_user_gets_tokens_and_an_account(api_client, mock_verify):
    response = google_login(api_client)

    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data
    assert User.objects.filter(email='salma@gmail.com').exists()


def test_new_user_has_no_usable_password(api_client, mock_verify):
    google_login(api_client)

    user = User.objects.get(email='salma@gmail.com')
    assert not user.has_usable_password()


def test_new_user_gets_the_name_from_google(api_client, mock_verify):
    google_login(api_client)

    user = User.objects.get(email='salma@gmail.com')
    assert user.first_name == 'Salma'
    assert user.last_name == 'Haddad'


def test_missing_name_is_saved_as_empty(api_client, google_info):
    # Some Google accounts have no family name
    del google_info['family_name']

    with patch(VERIFY_PATH, return_value=google_info):
        response = google_login(api_client)

    assert response.status_code == 200
    assert User.objects.get(email='salma@gmail.com').last_name == ''


def test_existing_user_logs_in_without_a_new_account(api_client, mock_verify):
    User.objects.create_user(email='salma@gmail.com', password='Old-pass-123')

    response = google_login(api_client)

    assert response.status_code == 200
    assert User.objects.count() == 1


def test_existing_user_keeps_their_password(api_client, mock_verify):
    user = User.objects.create_user(email='salma@gmail.com', password='Old-pass-123')

    google_login(api_client)

    user.refresh_from_db()
    assert user.check_password('Old-pass-123')


def test_email_case_does_not_create_a_second_account(api_client, mock_verify):
    User.objects.create_user(email='salma@gmail.com', password='Old-pass-123')
    mock_verify.return_value['email'] = 'Salma@Gmail.com'

    response = google_login(api_client)

    assert response.status_code == 200
    assert User.objects.count() == 1


def test_new_email_is_saved_in_lowercase(api_client, mock_verify):
    mock_verify.return_value['email'] = 'Salma@Gmail.com'

    google_login(api_client)

    assert User.objects.filter(email='salma@gmail.com').exists()


# --- Rejected ---

def test_invalid_token_is_rejected(api_client):
    # This is what the library raises for a forged, expired or foreign token
    with patch(VERIFY_PATH, side_effect=ValueError('Token expired')):
        response = google_login(api_client)

    assert response.status_code == 400
    assert 'id_token' in response.data
    assert not User.objects.exists()


def test_unverified_email_is_rejected(api_client, google_info):
    google_info['email_verified'] = False

    with patch(VERIFY_PATH, return_value=google_info):
        response = google_login(api_client)

    assert response.status_code == 400
    assert not User.objects.exists()


def test_missing_token_is_rejected(api_client, mock_verify):
    response = api_client.post(reverse('google_login'), {}, format='json')

    assert response.status_code == 400
    # Google is never asked when there is nothing to check
    mock_verify.assert_not_called()


def test_disabled_user_gets_no_tokens(api_client, mock_verify):
    User.objects.create_user(email='salma@gmail.com', password='Old-pass-123', is_active=False)

    response = google_login(api_client)

    assert response.status_code == 403
    assert 'access' not in response.data
    assert 'refresh' not in response.data


# --- Security ---

def test_token_is_checked_against_our_client_id(api_client, mock_verify):
    google_login(api_client, token='the-token-we-sent')

    args, kwargs = mock_verify.call_args
    assert args[0] == 'the-token-we-sent'
    assert kwargs['audience'] == CLIENT_ID


def test_returned_access_token_works_on_a_protected_endpoint(api_client, mock_verify):
    response = google_login(api_client)

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    me = api_client.get(reverse('me'))

    assert me.status_code == 200
    assert me.data['email'] == 'salma@gmail.com'


def test_google_login_is_rate_limited(api_client, mock_verify):
    for _ in range(10):
        assert google_login(api_client).status_code == 200

    assert google_login(api_client).status_code == 429