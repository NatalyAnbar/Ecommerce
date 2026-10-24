
"""Tests for PATCH/PUT /carts/<cart_pk>/items/<pk>/: editing a cart item."""

import pytest
from model_bakery import baker 
from cart import models
from cart.test.test_cartitem import helper


pytestmark = pytest.mark.django_db



def test_editing_sets_the_new_quantity(api_client, cart, product, item):
    response = api_client.patch(
                               helper.get_detail_url(cart , item),
                               helper.get_data(product.pk , quantity=10)
                               )
    assert response.status_code == 200
    item.refresh_from_db()
    # Editing replaces the quantity (10), it doesn't add to it (15)
    assert item.quantity == 10



def test_editing_cannot_switch_the_product(api_client, cart, product, item):
    other_product = baker.make(models.Product)
    response = api_client.patch(
                               helper.get_detail_url(cart , item),
                               helper.get_data(other_product.pk , quantity=10)
                               )
    assert response.status_code == 400
    assert 'product_id' in response.data
    item.refresh_from_db()
    assert item.product == product



@pytest.mark.parametrize('quantity' , [-5 , 0 , 150])
def test_editing_with_invalid_quantity_is_rejected(api_client, cart, product, quantity, item):
    response = api_client.patch(
                               helper.get_detail_url(cart , item),
                               helper.get_data(product.pk , quantity=quantity)
                               )
    assert response.status_code == 400
    assert 'quantity' in response.data
    item.refresh_from_db()
    assert item.quantity == 5



def test_put_is_not_allowed(api_client, cart, product, item):
    # PUT would require product_id on every edit; quantity changes use PATCH
    response = api_client.put(
                               helper.get_detail_url(cart , item),
                               helper.get_data(product.pk , quantity=10)
                               )
    assert response.status_code == 405
    item.refresh_from_db()
    assert item.quantity == 5