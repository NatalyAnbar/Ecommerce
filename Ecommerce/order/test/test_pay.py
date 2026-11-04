import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse
from rest_framework.test import APIClient

from order.models import Order
from payment.gateway import DECLINED_CARD, SUCCESS_CARD
from payment.models import Payment

pytestmark = pytest.mark.django_db


def get_url(order):
    return reverse('order-pay', args=[order.pk])


def get_cancel_url(order):
    return reverse('order-cancel', args=[order.pk])


def pay(client, order, card_number):
    return client.post(get_url(order), {'card_number': card_number}, format='json')


# --- Successful payment ---

def test_paying_with_success_card_returns_201(auth_client, order):
    response = pay(auth_client, order, SUCCESS_CARD)

    assert response.status_code == 201
    assert response.data['status'] == Payment.Status.SUCCEEDED


def test_successful_payment_marks_order_paid(auth_client, order):
    pay(auth_client, order, SUCCESS_CARD)

    order.refresh_from_db()
    assert order.status == Order.Status.PAID


def test_payment_amount_is_the_order_total(auth_client, order):
    response = pay(auth_client, order, SUCCESS_CARD)

    payment = Payment.objects.get(transaction_id=response.data['transaction_id'])
    assert payment.amount == order.total_price


def test_only_the_last_four_digits_are_kept(auth_client, order):
    response = pay(auth_client, order, SUCCESS_CARD)

    payment = Payment.objects.get(transaction_id=response.data['transaction_id'])
    assert payment.card_last4 == SUCCESS_CARD[-4:]
    # The full number is never sent back
    assert 'card_number' not in response.data


# --- Declined payment ---

def test_paying_with_declined_card_returns_402(auth_client, order):
    response = pay(auth_client, order, DECLINED_CARD)

    assert response.status_code