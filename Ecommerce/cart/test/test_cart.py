
"""Tests for /carts/: creating carts, who can read them, and the cart total."""

import pytest
from model_bakery import baker 
from cart import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from itertools import cycle


pytestmark = pytest.mark.django_db

User = get_user_model()


def get_list_url():
    return reverse('cart-list')


def get_detail_url(cart):
    return reverse('cart-detail', kwargs={'pk': cart.id})



def test_anonymous_user_can_create_cart(api_client):
    response = api_client.post(get_list_url(),{},format='json')

    assert response.status_code == 201
    assert models.Cart.objects.filter(id=response.data['id'],user=None).exists()



def test_logged_in_user_creates_their_own_cart(api_client,authenticate):
    user = authenticate()
    response = api_client.post(get_list_url(),{},format='json')

    assert response.status_code == 201
    assert models.Cart.objects.filter(id=response.data['id'],user=user).exists()



def test_user_cannot_have_two_carts(api_client,authenticate):
    user = authenticate()
    models.Cart.objects.create(user=user)
    response = api_client.post(get_list_url(),{},format='json')

    assert response.status_code == 400
    assert models.Cart.objects.count() == 1



def test_user_can_read_own_cart(api_client,authenticate):
    user = authenticate()
    cart = models.Cart.objects.create(user=user)
    response = api_client.get(get_detail_url(cart))

    assert response.status_code == 200
    # UUIDs come back as strings in the response
    assert response.data['id'] == str(cart.id)



def test_anonymous_user_can_read_anonymous_cart(api_client):
    cart = models.Cart.objects.create()
    response = api_client.get(get_detail_url(cart))

    assert response.status_code == 200



def test_anonymous_user_cannot_read_a_users_cart(api_client,authenticate):
    cart = models.Cart.objects.create(user=baker.make(User))
    response = api_client.get(get_detail_url(cart))

    assert response.status_code == 404



def test_user_cannot_read_another_users_cart(api_client, authenticate):
    authenticate()
    cart = models.Cart.objects.create(user=baker.make(User))
    response = api_client.get(get_detail_url(cart))

    assert response.status_code == 404



def test_cart_total_adds_up_every_line(api_client):
    # An anonymous cart, so the anonymous client can read it
    cart = baker.make(models.Cart)
    products = baker.make(models.Product  , _quantity=3 , price=cycle([100,200,300]))
    baker.make(models.CartItem , 
                        _quantity=3 , 
                        cart=cart , 
                        product=cycle(products) ,
                        quantity=cycle([1,2,3]))
    
    response = api_client.get(get_detail_url(cart))

    assert response.status_code == 200
    # 100×1 + 200×2 + 300×3, worked out by hand rather than with the same formula as the code
    assert response.data['total_price'] == 1400


