"""Tests for DELETE /carts/<cart_pk>/items/<pk>/: removing an item from a cart."""

import pytest
from model_bakery import baker
from cart import models
from cart.test.test_cartitem import helper


@pytest.mark.django_db
def test_deleting_removes_only_that_line(api_client, cart, product):
    item = baker.make(models.CartItem, cart=cart, product=product)
    other_item = baker.make(models.CartItem, cart=cart)

    response = api_client.delete(helper.get_detail_url(cart, item))

    assert response.status_code == 204
    assert not models.CartItem.objects.filter(pk=item.pk).exists()
    # The rest of the cart is untouched
    assert models.CartItem.objects.filter(pk=other_item.pk).exists()
    assert models.Cart.objects.filter(pk=cart.pk).exists()