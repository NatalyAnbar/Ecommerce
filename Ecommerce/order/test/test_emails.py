import pytest
from django.urls import reverse
from django.core import mail
from payment.gateway import SUCCESS_CARD, DECLINED_CARD

pytestmark = pytest.mark.django_db


def get_checkout_url():
    return reverse('order-checkout')


def get_payment_url(order):
    return reverse('order-pay',args=[order.pk])


def get_cancel_url(order):
    return reverse('order-cancel',args=[order.pk])


def test_checkout_emails_the_order(auth_client, cart_with_items, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_checkout_url(), {}, format='json')

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [cart_with_items.user.email]


def test_order_email_lists_every_item(auth_client, cart_with_items, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_checkout_url(), {}, format='json')

    body = mail.outbox[0].body
    assert '2 x Milk' in body
    assert '3 x T-shirt' in body


def test_failed_checkout_sends_no_email(auth_client, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_checkout_url(), {}, format='json')

    assert len(mail.outbox) == 0


def test_successful_payment_emails_the_customer(auth_client, order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_payment_url(order), {'card_number':SUCCESS_CARD}, format='json')

    body = mail.outbox[0].body
    assert 'Amount: 160' in  body
    assert f'**** {SUCCESS_CARD[-4:]}' in body


def test_payment_email_never_shows_the_full_card(auth_client, order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_payment_url(order), {'card_number':SUCCESS_CARD}, format='json')

    body = mail.outbox[0].body
    assert SUCCESS_CARD not in body


def test_declined_payment_sends_no_email(auth_client, order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_payment_url(order), {'card_number':DECLINED_CARD}, format='json')

    assert len(mail.outbox) == 0


def test_declined_payment_sends_no_email(auth_client, order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_payment_url(order), {'card_number':DECLINED_CARD}, format='json')

    assert len(mail.outbox) == 0


def test_cancel_emails_the_customer(auth_client, order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_cancel_url(order), {}, format='json')

    assert len(mail.outbox) == 1
    assert str(order.id) in mail.outbox[0].body


def test_rejected_cancel_sends_no_email(auth_client, paid_order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(get_cancel_url(paid_order), {}, format='json')

    assert len(mail.outbox) == 0


def test_no_email_is_sent_before_the_transaction_commits(auth_client, order, django_capture_on_commit_callbacks):

    with django_capture_on_commit_callbacks() as callbacks:
        auth_client.post(get_cancel_url(order), {}, format='json')

    # The email waits for the commit instead of going out straight away
    assert len(mail.outbox) == 0
    assert len(callbacks) == 1