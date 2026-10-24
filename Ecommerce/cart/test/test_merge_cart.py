"""Tests for POST /carts/merge/: moving an anonymous cart into the user's cart after login."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker

from cart import models
from store.models import Product


pytestmark = pytest.mark.django_db

User = get_user_model()


def merge(api_client, cart_id):
    return api_client.post(reverse('merge'), {'cart_id': str(cart_id)}, format='json')


@pytest.fixture
def guest_cart():
    """The anonymous cart the user filled before logging in."""
    return baker.make(models.Cart, user=None)



def test_merge_moves_items_into_the_users_cart(api_client, authenticate, guest_cart):
    user = authenticate()
    user_cart = baker.make(models.Cart, user=user)
    baker.make(models.CartItem, cart=user_cart, _quantity=2)
    baker.make(models.CartItem, cart=guest_cart, _quantity=3)

    response = merge(api_client, guest_cart.id)

    assert response.status_code == 200
    # 2 already there + 3 moved over, all different products
    assert user_cart.cart_items.count() == 5



def test_merge_deletes_the_anonymous_cart(api_client, authenticate, guest_cart):
    authenticate()
    baker.make(models.CartItem, cart=guest_cart, _quantity=3)

    response = merge(api_client, guest_cart.id)

    assert response.status_code == 200
    assert not models.Cart.objects.filter(pk=guest_cart.pk).exists()



def test_merge_creates_a_cart_if_the_user_has_none(api_client, authenticate, guest_cart):
    user = authenticate()
    baker.make(models.CartItem, cart=guest_cart, _quantity=3)

    response = merge(api_client, guest_cart.id)

    assert response.status_code == 200
    user_cart = models.Cart.objects.get(user=user)
    assert user_cart.cart_items.count() == 3



def test_merge_adds_up_a_product_in_both_carts(api_client, authenticate, guest_cart):
    user = authenticate()
    product = baker.make(Product)
    user_cart = baker.make(models.Cart, user=user)
    baker.make(models.CartItem, cart=user_cart, product=product, quantity=3)
    baker.make(models.CartItem, cart=guest_cart, product=product, quantity=2)

    response = merge(api_client, guest_cart.id)

    assert response.status_code == 200
    # One line for the product, not two
    line = user_cart.cart_items.get()
    assert line.quantity == 5



def test_merge_caps_the_combined_quantity_at_100(api_client, authenticate, guest_cart):
    user = authenticate()
    product = baker.make(Product)
    user_cart = baker.make(models.Cart, user=user)
    baker.make(models.CartItem, cart=user_cart, product=product, quantity=30)
    baker.make(models.CartItem, cart=guest_cart, product=product, quantity=80)

    response = merge(api_client, guest_cart.id)

    assert response.status_code == 200
    assert user_cart.cart_items.get().quantity == 100



def test_merge_requires_login(api_client, guest_cart):
    baker.make(models.CartItem, cart=guest_cart)

    response = merge(api_client, guest_cart.id)

    assert response.status_code == 401
    # Nothing happened: the anonymous cart and its items are still there
    assert guest_cart.cart_items.count() == 1



@pytest.mark.parametrize(
    'body',
    [{}, {'cart_id': '999'}, {'cart_id': 'abc'}],
    ids=['missing', 'number', 'not-a-uuid'],
)
def test_merge_rejects_a_missing_or_malformed_cart_id(api_client, authenticate, body):
    authenticate()

    response = api_client.post(reverse('merge'), body, format='json')

    assert response.status_code == 400
    assert 'cart_id' in response.data



def test_merge_returns_404_for_an_unknown_cart(api_client, authenticate):
    authenticate()

    # A well-formed id that no cart has
    response = merge(api_client, uuid.uuid4())

    assert response.status_code == 404



def test_merge_cannot_take_another_users_cart(api_client, authenticate):
    authenticate()
    others_cart = baker.make(models.Cart, user=baker.make(User))
    baker.make(models.CartItem, cart=others_cart, _quantity=3)

    response = merge(api_client, others_cart.id)

    assert response.status_code == 404
    # Their cart is untouched
    assert models.Cart.objects.filter(pk=others_cart.pk).exists()
    assert others_cart.cart_items.count() == 3