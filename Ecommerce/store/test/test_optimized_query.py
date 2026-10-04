import pytest
from model_bakery import baker 
from django.urls import reverse
from store import models

@pytest.mark.django_db
def test_category_list_avoids_n_plus_one_queries(api_client , django_assert_num_queries):
    """
    Listing categories with nested products and images runs a fixed number of queries.

    Expected queries:
        1. categories
        2. products of those categories (prefetched)
        3. images of those products (prefetched)
        4. count query from pagination
    """

    categories = baker.make(models.Category , _quantity=5)

    for category in categories:
        products = baker.make(models.Product , _quantity=10 , category=category)
        for product in products:
            images = baker.make(models.ProductImage , _quantity=4 , product=product)

    url = reverse('category-list')
    
    with django_assert_num_queries(4):
        api_client.get(url)


            


