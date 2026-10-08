import pytest
from model_bakery import baker 
from django.urls import reverse
from store import models
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def reviews_list_url(product):
    """Build the nested reviews list URL for the given product."""
    return reverse('product_review-list', kwargs={'product_slug': product.slug})


# ---------- Model constraints ----------


@pytest.mark.django_db
def test_user_cannot_review_same_product_twice():
    """The database rejects a second review by the same user for the same product."""

    user = baker.make(User)
    product = baker.make(models.Product)

    baker.make(models.Review, user=user, product=product)

    with pytest.raises(IntegrityError):
        baker.make(models.Review, user=user, product=product)


@pytest.mark.django_db
def test_user_can_review_different_products():
    """The unique constraint is per product, so one user can review many products."""

    user = baker.make(User)

    product1 = baker.make(models.Product)
    product2 = baker.make(models.Product)

    baker.make(models.Review, user=user, product=product1)
    baker.make(models.Review, user=user, product=product2)

    assert models.Review.objects.filter(user=user).count() == 2



# ---------- Read access ----------


@pytest.mark.django_db
def test_anonymous_user_can_read_product_reviews(api_client):
    """Anyone can list a product's reviews"""

    product = baker.make(models.Product)
    baker.make(models.Review , _quantity=5 , product=product)

    url = reviews_list_url(product)
    response = api_client.get(url)

    assert response.status_code == 200



# ---------- Write access ----------



@pytest.mark.django_db
def test_anonymous_user_cannot_create_review(api_client):
    """Unauthenticated users get 401 and nothing is saved."""

    product = baker.make(models.Product)
    url = reviews_list_url(product)
    response = api_client.post(url,format='json')
    assert response.status_code == 401
    assert not models.Review.objects.exists()


@pytest.mark.django_db
def test_authenticated_user_can_create_review(api_client,authenticate):
    """The review is saved with the requesting user and the product from the URL."""

    user = authenticate()
    product = baker.make(models.Product)
    url = reviews_list_url(product)
    response = api_client.post(url , {'rating':3} , format='json')
    assert response.status_code == 201
    assert models.Review.objects.filter(rating=3).exists()

