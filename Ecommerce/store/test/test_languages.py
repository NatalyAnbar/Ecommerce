import pytest
from django.urls import reverse

@pytest.mark.django_db
def test(api_client):
    url = reverse('category',args=['slug'])
    api_client.get(url,)