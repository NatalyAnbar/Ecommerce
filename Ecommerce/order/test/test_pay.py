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

    assert response.status_code == 402
    assert response.data['status'] == Payment.Status.FAILED


def test_declined_payment_keeps_order_pending(auth_client, order):
    pay(auth_client, order, DECLINED_CARD)

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING


def test_declined_payment_is_still_recorded(auth_client, order):
    pay(auth_client, order, DECLINED_CARD)

    assert Payment.objects.filter(order=order, status=Payment.Status.FAILED).count() == 1


def test_order_can_be_paid_after_a_declined_attempt(auth_client, order):
    pay(auth_client, order, DECLINED_CARD)
    response = pay(auth_client, order, SUCCESS_CARD)

    assert response.status_code == 201
    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert Payment.objects.filter(order=order).count() == 2


def test_unknown_card_is_declined(auth_client, order):
    response = pay(auth_client, order, '1111222233334444')

    assert response.status_code == 402


# --- Order status ---

def test_paid_order_cannot_be_paid_again(auth_client, paid_order):
    response = pay(auth_client, paid_order, SUCCESS_CARD)

    assert response.status_code == 400
    assert Payment.objects.filter(
        order=paid_order, status=Payment.Status.SUCCEEDED
    ).count() == 1


def test_cancelled_order_cannot_be_paid(auth_client, order):
    order.status = Order.Status.CANCELLED
    order.save(update_fields=['status'])

    response = pay(auth_client, order, SUCCESS_CARD)

    assert response.status_code == 400
    assert not Payment.objects.filter(order=order).exists()


def test_paid_order_cannot_be_cancelled(auth_client, paid_order):
    response = auth_client.post(get_cancel_url(paid_order))

    assert response.status_code == 400
    paid_order.refresh_from_db()
    assert paid_order.status == Order.Status.PAID


# --- Invalid card number ---

@pytest.mark.parametrize('card_number', [
    '123456789',            # too short
    '123456789123456789',   # too long
    '24242424242424fd',     # letters
    '',                     # empty
    None,                   # null
])
def test_invalid_card_number_is_rejected(auth_client, order, card_number):
    response = pay(auth_client, order, card_number)

    assert response.status_code == 400
    assert not Payment.objects.exists()


def test_missing_card_number_is_rejected(auth_client, order):
    response = auth_client.post(get_url(order), {}, format='json')

    assert response.status_code == 400
    assert not Payment.objects.exists()


# --- Who can pay ---

def test_anonymous_user_cannot_pay(order):
    response = pay(APIClient(), order, SUCCESS_CARD)

    assert response.status_code == 401


def test_cannot_pay_another_users_order(auth_client, other_order):
    response = pay(auth_client, other_order, SUCCESS_CARD)

    assert response.status_code == 404
    other_order.refresh_from_db()
    assert other_order.status == Order.Status.PENDING
    assert not Payment.objects.filter(order=other_order).exists()


def test_paying_a_missing_order_returns_404(auth_client):
    response = auth_client.post(
        reverse('order-pay', args=[999999]),
        {'card_number': SUCCESS_CARD},
        format='json',
    )

    assert response.status_code == 404


# --- Database rules ---

def make_payment(order, status):
    return Payment.objects.create(
        order=order, amount=order.total_price, status=status, card_last4='4242',
    )


def test_database_rejects_a_second_successful_payment(order):
    make_payment(order, Payment.Status.SUCCEEDED)

    # Wrapped so the failed insert doesn't break the rest of the test's transaction
    with pytest.raises(IntegrityError), transaction.atomic():
        make_payment(order, Payment.Status.SUCCEEDED)


def test_failed_attempts_are_unlimited(order):
    make_payment(order, Payment.Status.FAILED)
    make_payment(order, Payment.Status.FAILED)

    assert Payment.objects.filter(order=order).count() == 2


def test_order_with_payments_cannot_be_deleted(paid_order):
    with pytest.raises(ProtectedError):
        paid_order.delete()