import pytest
from model_bakery import baker 
from django.urls import reverse
from itertools import cycle
from store import models

# Prices are created deliberately out of order, so a passing test proves
# the API sorted them rather than returning them in insertion order.
UNSORTED_PRICES = [200, 100, 500, 400, 300]


@pytest.mark.django_db
def test_products_can_be_ordered_by_price_ascending(api_client):
    """?ordering=price returns the cheapest products first."""

    baker.make(models.Product , 
                price = cycle(UNSORTED_PRICES) ,
                _quantity=5)
    
    url = reverse('product-list')
    response = api_client.get(url,{'ordering':'price'})

    prices = [float(p['price']) for p in response.data['results']]
    assert prices == [100,200,300,400,500]


@pytest.mark.django_db
def test_products_can_be_ordered_by_price_descending(api_client):
    """?ordering=-price returns the most expensive products first."""
    
    baker.make(models.Product , 
                price = cycle(UNSORTED_PRICES) ,
                _quantity=5)
    
    url = reverse('product-list')
    response = api_client.get(url,{'ordering':'-price'})
    
    prices = [float(p['price']) for p in response.data['results']]
    assert prices == [500,400,300,200,100]