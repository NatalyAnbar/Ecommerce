"""Tests for signing up."""

import pytest
from django.urls import reverse
from model_bakery import baker 
from accounts import models


pytestmark = pytest.mark.django_db

def register_url():
    return reverse('register-list')

def get_data(**extra_fields):
    """Valid sign-up data. Pass keyword arguments to change any field."""
    return {
        'email' : 'test123@gmail.com',
        'first_name' : 'test_nat',
        'last_name' : 'test_anb',
        'password' : 'blabla@123',
        'confirm_password' : 'blabla@123'
    } | extra_fields



def test_register_creates_user_with_hashed_password(api_client):

    url = register_url()
    response = api_client.post(url,get_data(),format='json')

    print(response.data)

    assert response.status_code == 201
    user = models.User.objects.get(id=response.data['id'])
    assert user.check_password('blabla@123')
    assert user.password != 'blabla@123'



@pytest.mark.parametrize('kwargs',[
    {'password':'ttoott@@12@' , 'confirm_password':'ttoott@@1'},
    {'password':'nat@','confirm_password':'nat@'},
    {'password':'test','confirm_password':'test'},
    {'password':'12345','confirm_password':'22345'},
    {'password':'test@123','confirm_password':'test@123'}
])
def test_register_with_invalid_password_returns_400(api_client,kwargs):
    """Each password breaks exactly one rule."""

    url = register_url()
    response = api_client.post(url,get_data(**kwargs),format='json')

    assert response.status_code == 400
    assert 'password' in response.data or 'confirm_password' in response.data 
    assert not models.User.objects.exists()



def test_register_with_existing_email_returns_400(api_client):
    """Emails are compared case-insensitively, even for accounts saved before lowercasing."""

    baker.make(models.User , email='TEST123@Gmail.com')
    url = register_url()
    response = api_client.post(url,get_data(),format='json')

    assert response.status_code == 400
    assert 'email' in response.data
    assert models.User.objects.count() == 1



def test_register_ignores_admin_flags(api_client):
    """A client can't make itself staff or superuser."""
    url = register_url() 
    response = api_client.post(url,
                               get_data(is_staff=True , is_superuser=True),
                               format='json')
    
    assert response.status_code == 201
    user = models.User.objects.get(id=response.data['id'])
    assert user.is_staff == False
    assert user.is_superuser == False

