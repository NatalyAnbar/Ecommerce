import pytest
from django.urls import reverse
from model_bakery import baker 
from store import models

    


@pytest.mark.django_db
def test_category_name_follows_accept_language_header(api_client):
    """The localized category name matches the language requested by the client."""

    category = baker.make(models.Category,name_en = 'Electronics',name_ar = 'الكترونيات')

    url = reverse('category-detail',args=[category.slug])
    response_en = api_client.get(url,HTTP_ACCEPT_LANGUAGE = 'en', format='json')
    response_ar = api_client.get(url,HTTP_ACCEPT_LANGUAGE = 'ar', format='json')

    assert response_en.data['name'] == 'Electronics'
    assert response_ar.data['name'] == 'الكترونيات'


@pytest.mark.django_db
def test_category_name_falls_back_to_default_language(api_client):
    """Unsupported languages fall back to the default language (English)"""

    category = baker.make(models.Category,name_en = 'Electronics',name_ar = 'الكترونيات')
    url = reverse('category-detail',args=[category.slug])
    response = api_client.get(url,HTTP_ACCEPT_LANGUAGE='fr',format='json')

    assert response.status_code == 200
    assert response.data['name'] == 'Electronics'


@pytest.mark.django_db
def test_product_fields_follow_accept_language_header(api_client):
    """Localized product name and description match the requested language."""

    product = baker.make(models.Product , 
                         name_en='iphone' , name_ar='ايفون',
                         description_en='A great phone', description_ar='هاتف رائع')
    url = reverse('product-detail',args=[product.slug])

    response_en = api_client.get(url,HTTP_ACCEPT_LANGUAGE='en',format='json')
    response_ar = api_client.get(url,HTTP_ACCEPT_LANGUAGE='ar',format='json')

    assert response_en.data['name'] == 'iphone'
    assert response_ar.data['name'] == 'ايفون'

    assert response_en.data['description'] == 'A great phone'
    assert response_ar.data['description'] == 'هاتف رائع'

