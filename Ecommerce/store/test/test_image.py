"""Tests for the product image upload rules."""

import pytest
from model_bakery import baker 
from store import models
from store.test import helper
from django.urls import reverse


def get_product_image_url_list(product):
    return reverse('product-images-list',kwargs={'product_slug':product.slug})


def get_product_image_url_retrieve(product , image):
    """URL for reading, updating and deleting one product image."""
    return reverse('product-images-detail',kwargs={
        'product_slug' : product.slug,
        'pk' : image.pk
        })


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



# ------------- /product/image


# ---------------- Read -----------------------

@pytest.mark.django_db
def test_anyone_can_list_only_this_products_images(api_client):
    """Images of other products must not leak into the list."""
    product = baker.make(models.Product)
    baker.make(models.ProductImage, product=product, _quantity=3)
    baker.make(models.ProductImage, _quantity=2)  # belong to other products

    url = get_product_image_url_list(product)
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] == 3


@pytest.mark.django_db
def test_anyone_can_retrieve_product_image(api_client):
    product = baker.make(models.Product)
    image = baker.make(models.ProductImage , product=product)
    url = get_product_image_url_retrieve(product,image)
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['id'] == image.id


@pytest.mark.django_db
def test_retrieve_image_under_wrong_product_returns_404(api_client):
    """An image is only reachable under its own product's URL."""
    product = baker.make(models.Product)
    other_product = baker.make(models.Product)
    image = baker.make(models.ProductImage, product=product, img=helper.make_image())

    url = get_product_image_url_retrieve(other_product,image)
    response = api_client.get(url)

    assert response.status_code == 404


# --------------- Update ------------------

@pytest.mark.django_db
def test_patch_cannot_move_image_to_another_product(api_client,authenticate):
    """The request succeeds, but the product field is ignored."""

    authenticate('change_productimage')
    product = baker.make(models.Product)
    other_product = baker.make(models.Product)
    image = baker.make(models.ProductImage , img=helper.make_image() , product=product)

    url = get_product_image_url_retrieve(product,image)
    response = api_client.patch(url,
                                {'product' : other_product.id},
                                format='json')

    image.refresh_from_db()
    assert response.status_code == 200
    assert image.product != other_product
    assert image.product == product


@pytest.mark.django_db
def test_patch_updates_image_title(api_client,authenticate):
    """Titles stay editable after upload, without re-uploading the file."""
    authenticate('change_productimage')
    product = baker.make(models.Product)
    image = baker.make(models.ProductImage, 
                       img=helper.make_image(), 
                       product=product , 
                       title_en = 'iphone')

    url = get_product_image_url_retrieve(product,image)
    response = api_client.patch(url,
                                {'title_en' : 'samsung'},
                                format='json')
    
    image.refresh_from_db()
    assert response.status_code == 200
    assert image.title_en == 'samsung'


@pytest.mark.django_db
def test_patch_replaces_image_file(api_client,authenticate):
    """A new file can replace the old one without deleting the image record."""
    authenticate('change_productimage')
    product = baker.make(models.Product)
    image = baker.make(models.ProductImage, 
                       img=helper.make_image(name='old_img',extension='jpeg'), 
                       product=product)
    
    url = get_product_image_url_retrieve(product,image)
    response = api_client.patch(url,
                                {'img' : helper.make_image(name='new_img',extension='png')},
                                format='multipart')

    image.refresh_from_db()
    assert response.status_code == 200
    assert image.img.name == 'products/new_img.png'
    assert image.img.name.endswith('png')


# ---------------- Delete ------------
@pytest.mark.django_db
def test_admin_can_delete_product_image(api_client,authenticate):
    authenticate('delete_productimage')
    image = baker.make(models.ProductImage)
    url = get_product_image_url_retrieve(product=image.product , image=image)
    response = api_client.delete(url)

    assert response.status_code == 204
    assert not models.ProductImage.objects.filter(id=image.id).exists()


@pytest.mark.django_db
def test_anonymous_user_cannot_delete_product_image(api_client):
    image = baker.make(models.ProductImage, img=helper.make_image())

    url = get_product_image_url_retrieve(image.product , image)
    response = api_client.delete(url)

    assert response.status_code == 401
    assert models.ProductImage.objects.filter(id=image.id).exists()


@pytest.mark.django_db
def test_user_without_permission_cannot_delete_product_image(api_client, authenticate):
    authenticate()
    image = baker.make(models.ProductImage, img=helper.make_image())

    url = get_product_image_url_retrieve(image.product , image)
    response = api_client.delete(url)

    assert response.status_code == 403
    assert models.ProductImage.objects.filter(id=image.id).exists()