import pytest
from model_bakery import baker 
from cart import models
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


def get_url(cart):
    return reverse('cart-clear', kwargs={'pk': str(cart.id)})


@pytest.mark.django_db
def test_clearing_empties_the_cart_but_keeps_it(api_client):
    cart = baker.make(models.Cart)
    baker.make(models.CartItem , _quantity=5 , cart=cart)
    
    response = api_client.delete(get_url(cart))
    assert response.status_code == 204
    assert cart.cart_items.count() == 0
    # Emptied, not deleted
    assert models.Cart.objects.filter(pk=cart.pk).exists()


@pytest.mark.django_db
def test_user_cannot_clear_another_users_cart(api_client, authenticate):
    authenticate()
    others_cart = baker.make(models.Cart, user=baker.make(User))
    baker.make(models.CartItem, cart=others_cart, _quantity=2)

    response = api_client.delete(get_url(others_cart))

    assert response.status_code == 404
    assert others_cart.cart_items.count() == 2