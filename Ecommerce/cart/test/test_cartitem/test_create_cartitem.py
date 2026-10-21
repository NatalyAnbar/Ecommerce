
"""Tests for POST /carts/<cart_pk>/items/: adding products to a cart."""

import pytest
from model_bakery import baker 
from cart import models
from cart.test.test_cartitem import helper


@pytest.mark.django_db
def test_adding_a_product_creates_an_item(api_client, cart, product):
    response = api_client.post(
                               helper.get_list_url(cart),
                               helper.get_data(product.pk , quantity=5),
                               format='json'
                               )
    assert response.status_code == 201
    item = models.CartItem.objects.get(cart=cart, product=product)
    assert item.quantity == 5


@pytest.mark.django_db
def test_quantity_defaults_to_one(api_client, cart, product):
    response = api_client.post(
                               helper.get_list_url(cart),
                               helper.get_data(product.pk),
                               format='json'
                               )
    assert response.status_code == 201
    assert response.data['quantity'] == 1
    item = models.CartItem.objects.get(id=response.data['id'])
    assert item.quantity == 1


@pytest.mark.django_db
def test_adding_the_same_product_raises_its_quantity(api_client, cart, product):
    baker.make(models.CartItem, cart=cart, product=product, quantity=10)
    response = api_client.post(
                               helper.get_list_url(cart),
                               helper.get_data(product.pk , quantity=5),
                               format='json'
                               )

    assert response.status_code == 201 
    assert response.data['quantity'] == 15
    # Still one line for this product, not a second one
    assert models.CartItem.objects.filter(cart=cart, product=product).count() == 1
    assert models.CartItem.objects.get(cart=cart, product=product).quantity == 15


@pytest.mark.django_db
def test_adding_a_missing_product_is_rejected(api_client, cart):
    response = api_client.post(helper.get_list_url(cart),
                               helper.get_data(999),
                               format='json'
                               )
    assert response.status_code == 400
    assert 'product_id' in response.data
    assert models.CartItem.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('quantity' , [200, -1, 0])
def test_adding_with_invalid_quantity_is_rejected(api_client, cart, product, quantity):
    response = api_client.post(helper.get_list_url(cart),
                               helper.get_data(product.id , quantity=quantity),
                               format='json'
                               )
    assert response.status_code == 400
    assert 'quantity' in response.data
    assert models.CartItem.objects.count() == 0


@pytest.mark.django_db
def test_adding_past_100_in_total_is_rejected(api_client, cart, product):
    item = baker.make(models.CartItem, cart=cart, product=product, quantity=80)

    # 80 already in the cart + 30 more = 110; 30 alone is fine, the total isn't
    response = api_client.post(helper.get_list_url(cart), helper.get_data(product.pk, quantity=30), format='json')

    assert response.status_code == 400
    assert 'quantity' in response.data
    item.refresh_from_db()
    assert item.quantity == 80