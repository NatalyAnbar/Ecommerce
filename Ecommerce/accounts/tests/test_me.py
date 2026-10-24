
"""Tests for the logged-in user's profile."""

import pytest
from django.urls import reverse
from model_bakery import baker 
from accounts import models


pytestmark = pytest.mark.django_db


def me_url():
    return reverse('me')


@pytest.fixture
def user(api_client):
    """A logged-in user with a known name."""
    user = baker.make(models.User, first_name='Nataly', last_name='Alanbar')
    api_client.force_authenticate(user=user)
    return user



def test_anonymous_user_cannot_see_profile(api_client):
    response = api_client.get(me_url())

    assert response.status_code == 401



def test_user_sees_own_profile(api_client, user):

    response = api_client.get(me_url())

    assert response.status_code == 200
    assert response.data['id'] == user.id
    assert response.data['email'] == user.email



def test_user_can_update_first_name(api_client, user):

    response = api_client.patch(me_url(),{'first_name':'Nancy'})

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == 'Nancy'



def test_user_cannot_change_email_through_profile(api_client, user):
    """The request succeeds, but the email field is ignored."""
    old_email = user.email

    response = api_client.patch(me_url(), {'email': 'new@example.com'}, format='json')

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.email == old_email
