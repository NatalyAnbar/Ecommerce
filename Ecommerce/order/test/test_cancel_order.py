import pytest
from django.urls import reverse

from order.models import Order

pytestmark = pytest.mark.django_db


def get_cancel_url(order):
    return reverse('order-cancel', kwargs={'pk': order.pk})


def test_cancel_pending_order(auth_client, order):
    response = auth_client.post(get_cancel_url(order), {}, format='json')

    assert response.status_code == 200
    assert response.data['status'] == Order.Status.CANCELLED
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED


@pytest.mark.parametrize('order_status', [Order.Status.PAID, Order.Status.CANCELLED])
def test_cancel_non_pending_order_returns_400(auth_client, order, order_status):
    order.status = order_status
    order.save(update_fields=['status'])

    response = auth_client.post(get_cancel_url(order), {}, format='json')

    assert response.status_code == 400
    order.refresh_from_db()
    assert order.status == order_status


def test_cancel_another_users_order_returns_404(auth_client, other_order):
    response = auth_client.post(get_cancel_url(other_order), {}, format='json')

    assert response.status_code == 404
    other_order.refresh_from_db()
    assert other_order.status == Order.Status.PENDING


def test_cancel_requires_authentication(api_client, order):
    response = api_client.post(get_cancel_url(order), {}, format='json')

    assert response.status_code == 401
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING