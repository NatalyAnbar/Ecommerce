import pytest
from model_bakery import baker 
from django.urls import reverse
from itertools import cycle
from store import models


@pytest.mark.django_db
def test_products_can_be_filtered_by_price_range(api_client):
    """Only products priced within the requested range are returned."""
    
    baker.make(models.Product , 
                    price = cycle([100,200,300,400,500]),
                    _quantity = 5)

    url = reverse('product-list')
    response = api_client.get(url,
                              {'price_min' : 200 , 'price_max' : 400},
                              format='json')

    prices = sorted([float(p['price']) for p in response.data['results']])
    assert prices == [200.0,300.0,400.0]
    

