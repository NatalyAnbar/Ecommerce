
"""Tests for PUT /accounts/change-password/."""

import pytest
from django.urls import reverse
from accounts import models


pytestmark = pytest.mark.django_db

OLD_PASSWORD = 'test@1234'
NEW_PASSWORD = '1234@test'


# Each case breaks exactly one rule and keeps the rest valid,
# so the 400 can only come from that rule.
INVALID_CHANGES = [
                        (
                            {
                                'old_password':'test@test' , 
                                'new_password':NEW_PASSWORD , 
                                'confirm_new_password':NEW_PASSWORD
                            }, 
                            'old_password'
                        ),
                        (
                            {
                                'old_password':OLD_PASSWORD , 
                                'new_password':NEW_PASSWORD , 
                                'confirm_new_password':'test@test'
                            },
                            'confirm_new_password'
                        ),
                        (
                            {
                                # Both new fields match, so only the strength check fails
                                'old_password':OLD_PASSWORD , 
                                'new_password':'1234' , 
                                'confirm_new_password':'1234'
                            },
                            'new_password'
                        )
                    ]

def get_url():
    return reverse('change_password')


def get_data(**updated_fields):
    """A valid request body; a test passes only the fields it wants to change."""
    return {
        'old_password' : OLD_PASSWORD , 
        'new_password' : NEW_PASSWORD , 
        'confirm_new_password': NEW_PASSWORD
        } | updated_fields


def create_user():
    """Create a user with OLD_PASSWORD, hashed the same way a real sign-up would."""
    return models.User.objects.create_user(email='test@gmail.com', password=OLD_PASSWORD)


@pytest.fixture
def user(api_client):
    """A logged-in user whose current password is OLD_PASSWORD."""
    user = create_user()
    api_client.force_authenticate(user=user)
    return user



def test_user_can_change_password(api_client , user):

    response = api_client.put(get_url() , get_data() , format='json')

    assert response.status_code == 200
    user.refresh_from_db()    
    assert user.check_password(NEW_PASSWORD)



def test_anonymous_user_cannot_change_password(api_client):
    """ Created without logging in, so the request has no token """

    user = create_user()
    response = api_client.put(get_url() , get_data() , format='json')

    assert response.status_code == 401
    user.refresh_from_db()
    assert user.check_password(OLD_PASSWORD)



def test_patch_is_not_allowed(api_client, user):
    """ PATCH would make the fields optional, so the view only accepts PUT """
    response = api_client.patch(get_url() , get_data() , format='json')

    user.refresh_from_db()
    assert response.status_code == 405
    assert user.check_password(OLD_PASSWORD)



@pytest.mark.parametrize('data, error_field',
                         INVALID_CHANGES)

def test_invalid_change_is_rejected(api_client, user, data, error_field):

    response = api_client.put(get_url(),get_data(**data),format='json')

    user.refresh_from_db()
    assert response.status_code == 400
    assert error_field in response.data
    assert user.check_password(OLD_PASSWORD)



