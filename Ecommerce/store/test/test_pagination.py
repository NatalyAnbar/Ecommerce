import pytest
from model_bakery import baker 
from django.urls import reverse
from store import models

@pytest.mark.django_db
def test_client_can_choose_page_size(api_client):
    """The page_size query parameter controls how many products a page returns."""

    baker.make(models.Product , _quantity=100)
    response = api_client.get(reverse('product-list'),{'page_size':20})

    assert response.status_code == 200
    assert len(response.data['results']) == 20


@pytest.mark.django_db
def test_page_size_is_capped_at_maximum(api_client):
    """Requests above max_page_size (30) are capped, protecting the server from huge pages."""

    baker.make(models.Product , _quantity=100)
    url = reverse('product-list')
    response = api_client.get(url,{'page_size':50})

    assert response.status_code == 200
    assert len(response.data['results']) == 30
