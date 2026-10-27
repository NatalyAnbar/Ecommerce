import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_login_is_limited_to_five_attempts_per_minute(api_client):
    data = {'email': 'someone@example.com', 'password': 'wrong-password'}

    # The first five attempts are allowed (they fail).
    for _ in range(5):
        response = api_client.post(reverse('login'), data, format='json')
        assert response.status_code == 401

    # The sixth one is blocked.
    response = api_client.post(reverse('login'), data, format='json')
    assert response.status_code == 429