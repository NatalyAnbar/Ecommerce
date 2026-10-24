import pytest
from model_bakery import baker 
from django.urls import reverse
from store import models
from django.contrib.auth import get_user_model
from django.db import IntegrityError


pytestmark = pytest.mark.django_db

User = get_user_model()

def reviews_detail_url(product , review):
    return reverse('product_review-detail', 
                   kwargs={'product_slug': product.slug, 
                           'pk': review.pk})


def reviews_list_url(product):
    """Build the nested reviews list URL for the given product."""
    return reverse('product_review-list', kwargs={'product_slug': product.slug})


# ---------- Model constraints ----------

def test_user_cannot_review_same_product_twice():
    """The database rejects a second review by the same user for the same product."""

    user = baker.make(User)
    product = baker.make(models.Product)

    baker.make(models.Review, user=user, product=product)

    with pytest.raises(IntegrityError):
        baker.make(models.Review, user=user, product=product)

def test_user_can_review_different_products():
    """The unique constraint is per product, so one user can review many products."""

    user = baker.make(User)

    product1 = baker.make(models.Product)
    product2 = baker.make(models.Product)

    baker.make(models.Review, user=user, product=product1)
    baker.make(models.Review, user=user, product=product2)

    assert models.Review.objects.filter(user=user).count() == 2



# ---------- Read access ----------

def test_anonymous_user_can_read_product_reviews(api_client):
    """Anyone can list a product's reviews"""

    product = baker.make(models.Product)
    baker.make(models.Review , _quantity=5 , product=product)

    url = reviews_list_url(product)
    response = api_client.get(url)

    assert response.status_code == 200



# ---------- Write access ----------


def test_anonymous_user_cannot_create_review(api_client):
    """Unauthenticated users get 401 and nothing is saved."""

    product = baker.make(models.Product)
    url = reviews_list_url(product)
    response = api_client.post(url,format='json')
    assert response.status_code == 401
    assert not models.Review.objects.exists()

def test_authenticated_user_can_create_review(api_client, authenticate):
    """The review is saved with the requesting user and the product from the URL."""
    user = authenticate()
    product = baker.make(models.Product)

    response = api_client.post(reviews_list_url(product), {'rating': 3}, format='json')

    assert response.status_code == 201
    review = models.Review.objects.get(id=response.data['id'])
    assert review.user == user
    assert review.product == product

def test_owner_can_update_own_review(api_client, authenticate):
    """The author can edit their review."""

    user = authenticate()
    product = baker.make(models.Product)
    review = baker.make(models.Review, user=user, product=product, rating=3)

    response = api_client.patch(
        reviews_detail_url(product , review),
        {'rating': 5},
        format='json'
    )

    assert response.status_code == 200
    review.refresh_from_db()
    assert review.rating == 5

def test_reviews_show_the_reviewers_first_name_not_their_email(api_client):
    user = baker.make(User , email='test@gmail.com' , first_name='test')
    product = baker.make(models.Product)
    baker.make(models.Review , user=user , product=product)
    response = api_client.get(reviews_list_url(product))

    assert response.status_code == 200
    # Exactly the public fields: adding email (or anything else) here would fail this
    assert response.data['results'][0]['user'] == {'first_name': 'test'}
    assert 'test@gmail.com' not in str(response.data)
    