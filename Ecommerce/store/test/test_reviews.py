import pytest
from model_bakery import baker 
from store import models
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@pytest.mark.django_db
def test_user_cannot_review_same_product_twice():
    """The database rejects a second review by the same user for the same product."""

    user = baker.make(User)
    product = baker.make(models.Product)

    baker.make(models.Review, user=user, product=product)

    with pytest.raises(IntegrityError):
        baker.make(models.Review, user=user, product=product)


@pytest.mark.django_db
def test_user_can_reviews_diffrent_products():
    user = baker.make(User)

    product1 = baker.make(models.Product)
    product2 = baker.make(models.Product)

    baker.make(models.Review, user=user, product=product1)
    baker.make(models.Review, user=user, product=product2)

    assert models.Review.objects.filter(user=user).count() == 2

