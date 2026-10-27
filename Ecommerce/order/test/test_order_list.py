import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def get_list_url():
    return reverse('order-list')


def get_detail_url(order):
    return reverse('order-detail', kwargs={'pk': order.pk})


def test_list_returns_only_my_orders(auth_client, order, other_order):
    response = auth_client.get(get_list_url())

    assert response.status_code == 200
    ids = [item['id'] for item in response.data['results']]
    assert ids == [order.id]


def test_retrieve_my_order_returns_its_items(auth_client, order):
    response = auth_client.get(get_detail_url(order))

    assert response.status_code == 200
    assert len(response.data['order_items']) == 2


def test_retrieve_another_users_order_returns_404(auth_client, other_order):
    response = auth_client.get(get_detail_url(other_order))

    assert response.status_code == 404


def test_list_requires_authentication(api_client, order):
    response = api_client.get(get_list_url())

    assert response.status_code == 401