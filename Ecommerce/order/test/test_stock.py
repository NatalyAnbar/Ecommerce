import pytest
from django.urls import reverse
from order.models import Order

pytestmark = pytest.mark.django_db


def checkout(client):
    return client.post(reverse('order-checkout'), {}, format='json')


def cancel(client, order):
    return client.post(reverse('order-cancel', kwargs={'pk': order.pk}), {}, format='json')


def test_checkout_takes_the_stock(auth_client, cart_with_items, product, other_product):
    checkout(auth_client)

    product.refresh_from_db()
    other_product.refresh_from_db()
    # Cart: 2 x Milk, 3 x T-shirt; both start at 10.
    assert product.stock == 8
    assert other_product.stock == 7


def test_checkout_with_not_enough_stock_returns_400(auth_client, cart_with_items, other_product):
    other_product.stock = 1
    other_product.save()

    response = checkout(auth_client)

    assert response.status_code == 400
    assert response.data['products'] == ['T-shirt']


def test_checkout_with_not_enough_stock_changes_nothing(auth_client, cart_with_items, product, other_product):
    # Milk is available, T-shirt isn't: the whole order is refused.
    other_product.stock = 1
    other_product.save()

    checkout(auth_client)

    product.refresh_from_db()
    assert Order.objects.count() == 0
    assert product.stock == 10
    assert cart_with_items.cart_items.count() == 2


def test_cancel_puts_the_stock_back(auth_client, order, product, other_product):
    # The order fixture has 2 x Milk and 3 x T-shirt; both products have 10.
    cancel(auth_client, order)

    product.refresh_from_db()
    other_product.refresh_from_db()
    assert product.stock == 12
    assert other_product.stock == 13


def test_cancel_refused_does_not_touch_the_stock(auth_client, order, product):
    order.status = Order.Status.PAID
    order.save()

    cancel(auth_client, order)

    product.refresh_from_db()
    assert product.stock == 10