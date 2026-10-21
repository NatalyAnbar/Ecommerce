import pytest
from model_bakery import baker 
from cart import models

@pytest.fixture
def cart():
    """An anonymous cart, so the anonymous test client is allowed to use it."""
    return baker.make(models.Cart)


@pytest.fixture
def product():
    return baker.make(models.Product)


@pytest.fixture
def item(cart, product):
    """A line with 5 of the product, in the anonymous cart the test client can use."""
    return baker.make(models.CartItem, cart=cart, product=product, quantity=5)