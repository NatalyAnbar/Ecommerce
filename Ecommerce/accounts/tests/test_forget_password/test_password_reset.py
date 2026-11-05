import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse

pytestmark = pytest.mark.django_db


def get_url():
    return reverse('password_reset')


def request_reset(client, email):
    return client.post(get_url(), {'email': email}, format='json')


def test_existing_email_receives_a_reset_link(api_client, user):
    response = request_reset(api_client, user.email)

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]


def test_reset_email_contains_the_link_uid_and_token(api_client, user):
    request_reset(api_client, user.email)

    body = mail.outbox[0].body
    assert settings.PASSWORD_RESET_URL in body
    assert 'uid=' in body
    assert 'token=' in body


def test_email_lookup_ignores_letter_case(api_client, user):
    response = request_reset(api_client, user.email.upper())

    assert response.status_code == 200
    assert len(mail.outbox) == 1


def test_unknown_email_sends_nothing(api_client):
    response = request_reset(api_client, 'nobody@example.com')

    assert response.status_code == 200
    assert len(mail.outbox) == 0


def test_known_and_unknown_emails_get_the_same_response(api_client, user):
    known = request_reset(api_client, user.email)
    unknown = request_reset(api_client, 'nobody@example.com')

    # Nothing in the answer tells which emails have an account
    assert known.status_code == unknown.status_code
    assert known.data == unknown.data


def test_malformed_email_is_rejected(api_client):
    response = request_reset(api_client, 'nataly')

    assert response.status_code == 400
    assert len(mail.outbox) == 0


def test_reset_requests_are_rate_limited(api_client, user):
    for _ in range(5):
        assert request_reset(api_client, user.email).status_code == 200

    response = request_reset(api_client, user.email)

    assert response.status_code == 429