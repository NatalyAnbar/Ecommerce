import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from cart.models import Cart, CartItem
from order.models import Order, OrderItem
from store.models import Product

User = get_user_model()


# ---------- users ----------

@pytest.fixture
def user():
    """The customer the tests act as."""
    return baker.make(User, first_name='Nat', last_name='Anb')


@pytest.fixture
def other_user():
    """Someone else, for ownership checks."""
    return baker.make(User)


@pytest.fixture
def auth_client(api_client, user):
    """A client logged in as `user`."""
    # force_authenticate returns None, so return the client itself.
    api_client.force_authenticate(user=user)
    return api_client


# ---------- products ----------

@pytest.fixture
def product():
    return baker.make(Product, name_en='Milk', price=5, stock=10)


@pytest.fixture
def other_product():
    return baker.make(Product, name_en='T-shirt', price=50, stock=10)


# ---------- cart ----------

@pytest.fixture
def cart_with_items(user, product, other_product):
    """user's cart: 2 x Milk (5) + 3 x T-shirt (50) = 160."""
    cart = baker.make(Cart, user=user)
    baker.make(CartItem, cart=cart, product=product, quantity=2)
    baker.make(CartItem, cart=cart, product=other_product, quantity=3)
    return cart


# ---------- orders ----------

@pytest.fixture
def order(user, product, other_product):
    """A pending order of user's: 2 x Milk (5) + 3 x T-shirt (50) = 160."""
    order = baker.make(Order, user=user)
    baker.make(OrderItem, order=order, product=product, quantity=2, unit_price=5)
    baker.make(OrderItem, order=order, product=other_product, quantity=3, unit_price=50)
    return order


@pytest.fixture
def other_order(other_user):
    """A pending order that belongs to someone else."""
    return baker.make(Order, user=other_user)