"""Tests for the product image upload rules."""

import pytest
from model_bakery import baker 
from store import models
from store.test import helper

def prepare():
    """Create a category and return it with the product list URL."""
    category = baker.make(models.Category)
    url = helper.product_list_url()
    return category,url


@pytest.mark.django_db
@pytest.mark.parametrize(
    'image_kwargs',[
    {},                                  # default size and PNG
    {'width':700 , 'height':700},
    {'size_mb':4},                       # under the size limit
    {'width':500 , 'height':1000},       # at the max aspect ratio
    {'extension':'webp'}, 
    {'extension':'png'},
    {'extension':'jpeg'},
    {'extension':'jpg'},
    ])
def test_upload_valid_image_returns_201(api_client,authenticate,image_kwargs):
    """Images on the edge of each rule are still accepted."""

    authenticate('add_product')
    category, url = prepare()

    image = helper.make_image(**image_kwargs)
    response = api_client.post(url,
                               helper.get_payload(category=category,uploaded_img=[image]),
                               format='multipart')
    assert response.status_code == 201
    product = models.Product.objects.get(slug=response.data['slug'])
    assert product.images.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'image_kwargs', [
    {'width': 100, 'height': 100},       # too small
    {'width': 6000, 'height': 6000},     # too large
    {'width': 500, 'height': 1500},      # too stretched
    {'size_mb': 10},                     # file too heavy
    {'extension': 'gif'},
    {'extension': 'bmp'},
    {'extension': 'tiff'},               # extension not allowed
])
def test_upload_invalid_image_returns_400(api_client, authenticate, image_kwargs):
    """Each image breaks exactly one rule, so the rejection can only come from that rule."""

    authenticate('add_product')
    category, url = prepare()
    image = helper.make_image(**image_kwargs)

    response = api_client.post(
        url,
        helper.get_payload(category=category, uploaded_img=[image]),
        format='multipart',
    )

    assert response.status_code == 400
    assert 'uploaded_img' in response.data
    assert not models.Product.objects.exists()


@pytest.mark.django_db
def test_more_than_8_images(api_client,authenticate):
    """The product must not be saved either, so a retry doesn't create a duplicate."""

    authenticate('add_product')

    category, url = prepare()
    images = [helper.make_image(name=f'test{i}') for i in range(10)]

    response = api_client.post(url,
                            helper.get_payload(category=category,uploaded_img=images),
                            format='multipart')

    assert response.status_code == 400
    assert 'uploaded_img' in response.data
    assert not models.Product.objects.exists()


