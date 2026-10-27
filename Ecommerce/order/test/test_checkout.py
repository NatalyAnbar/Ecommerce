from decimal import Decimal

import pytest
from django.urls import reverse
from model_bakery import baker

from cart.models import Cart
from order.models import Order

pytestmark = pytest.mark.django_db


def get_checkout_url():
    return reverse('order-checkout')


def checkout(client):
    return client.post(get_checkout_url(), {}, format='json')


# ---------- success ----------

def test_checkout_creates_a_pending_order(auth_client, user, cart_with_items):
    response = checkout(auth_client)

    assert response.status_code == 201
    order = Order.objects.get(user=user)
    assert order.status == Order.Status.PENDING


def test_checkout_copies_cart_items_to_the_order(auth_client, user, cart_with_items, product, other_product):
    checkout(auth_client)

    order = Order.objects.get(user=user)
    assert order.order_items.count() == 2
    assert order.order_items.get(product=product).quantity == 2
    assert order.order_items.get(product=other_product).quantity == 3


def test_checkout_saves_the_current_product_price(auth_client, user, cart_with_items, product, other_product):
    checkout(auth_client)

    order = Order.objects.get(user=user)
    assert order.order_items.get(product=product).unit_price == Decimal('5')
    assert order.order_items.get(product=other_product).unit_price == Decimal('50')


def test_checkout_empties_the_cart(auth_client, cart_with_items):
    response = checkout(auth_client)

    assert response.status_code == 201
    assert cart_with_items.cart_items.count() == 0


def test_checkout_returns_the_correct_total(auth_client, cart_with_items):
    response = checkout(auth_client)

    # 2 x 5 + 3 x 50
    assert response.data['total_price'] == Decimal('160')


def test_order_keeps_its_price_after_product_price_changes(auth_client, user, cart_with_items, product):
    checkout(auth_client)

    product.price = 100
    product.save()

    order = Order.objects.get(user=user)
    assert order.order_items.get(product=product).unit_price == Decimal('5')


# ---------- refused ----------

def test_checkout_with_empty_cart_returns_400(auth_client, user):
    baker.make(Cart, user=user)

    response = checkout(auth_client)

    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_checkout_without_a_cart_returns_400(auth_client):
    response = checkout(auth_client)

    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_checkout_requires_authentication(api_client, cart_with_items):
    response = checkout(api_client)

    assert response.status_code == 401
    assert Order.objects.count() == 0