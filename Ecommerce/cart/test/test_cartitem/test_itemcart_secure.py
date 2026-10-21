
"""Tests that a cart's items can only be reached through your own cart."""

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from cart import models
from cart.test.test_cartitem import helper

User = get_user_model()


@pytest.fixture
def others_cart():
    """A cart that belongs to someone else (user)."""
    return baker.make(models.Cart, user=baker.make(User))


@pytest.fixture
def others_item(others_cart, product):
    """An item inside user's cart, so only the ownership check can block the request."""
    return baker.make(models.CartItem, cart=others_cart, product=product, quantity=5)


@pytest.mark.django_db
def test_anonymous_user_cannot_read_a_users_cart_items(api_client, others_cart):
    response = api_client.get(helper.get_list_url(others_cart))

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_read_another_users_cart_items(api_client, authenticate, others_cart):
    authenticate()

    response = api_client.get(helper.get_list_url(others_cart))

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_add_to_another_users_cart(api_client, authenticate, others_cart, product):
    authenticate()

    response = api_client.post(
        helper.get_list_url(others_cart), helper.get_data(product.pk, quantity=10), format='json'
    )

    assert response.status_code == 404
    assert models.CartItem.objects.filter(cart=others_cart).count() == 0


@pytest.mark.django_db
def test_user_cannot_edit_another_users_cart_item(api_client, authenticate, others_cart, others_item):
    authenticate()

    response = api_client.patch(
        helper.get_detail_url(others_cart, others_item), {'quantity': 10}, format='json'
    )

    assert response.status_code == 404
    others_item.refresh_from_db()
    assert others_item.quantity == 5


@pytest.mark.django_db
def test_user_cannot_delete_another_users_cart_item(api_client, authenticate, others_cart, others_item):
    authenticate()

    response = api_client.delete(helper.get_detail_url(others_cart, others_item))

    assert response.status_code == 404
    assert models.CartItem.objects.filter(pk=others_item.pk).exists()