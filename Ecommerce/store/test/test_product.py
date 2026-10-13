import pytest
from model_bakery import baker 
from django.urls import reverse
from store.test import helper
from store import models


def product_detail_url(product):
    return reverse('product-detail', kwargs={'slug': product.slug})


# ------------ create -----------------------

@pytest.mark.django_db
def test_product_manager_can_create_product_with_images(api_client,authenticate):
    """Users with add_product can create a product, and its uploaded images are saved."""

    authenticate('add_product')
    url = helper.product_list_url()
    category = baker.make(models.Category)
    img1 = helper.make_image(500,500,'img1.png')
    img2 = helper.make_image(500,500,'img2.png')

    response = api_client.post(url, 
                               helper.get_payload(category,uploaded_img=[img1,img2]), 
                               format='multipart')

    product = models.Product.objects.get(slug = response.data['slug'])
    assert response.status_code == 201
    assert product.images.count() == 2


@pytest.mark.django_db
def test_anonymous_user_cannot_create_product(api_client):
    """Unauthenticated users get 401 and nothing is saved."""

    url = helper.product_list_url()
    category = baker.make(models.Category)
    response = api_client.post(url,
                               helper.get_payload(category),
                               format='json')

    assert response.status_code == 401
    assert not models.Product.objects.exists()


# --------------- Read -----------

@pytest.mark.django_db
def test_anyone_can_list_products(api_client):
    """The product list is public and returns every product."""

    baker.make(models.Product,_quantity=5)
    url = helper.product_list_url()
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] == 5


@pytest.mark.django_db
def test_anyone_can_retrieve_product_by_slug(api_client):
    """A single product is public and looked up by its slug."""

    product = baker.make(models.Product)
    url = product_detail_url(product)
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['slug'] == product.slug


# ----------- Update -----------

@pytest.mark.django_db
def test_product_manager_can_update_product(api_client,authenticate):
    """Users with change_product can replace a product's data."""

    authenticate('change_product')
    product = baker.make(models.Product , name_en='iphone')
    category = baker.make(models.Category)

    url = product_detail_url(product)
    response = api_client.put(url,
                                 helper.get_payload(category, price=200, name_en='Ferrari', name_ar='فيراري'),
                                 format='json')

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.name_ar == 'فيراري'
    assert product.name_en == 'Ferrari'


@pytest.mark.django_db
def test_anonymous_user_cannot_update_product(api_client):
    """Unauthenticated users get 401 and the product is unchanged."""

    product = baker.make(models.Product , name_en='iPhone')
    category = baker.make(models.Category)

    url = product_detail_url(product)
    response = api_client.put(url,
                                 helper.get_payload(category, name_en='Ferrari'),
                                 format='json')

    assert response.status_code == 401
    product.refresh_from_db()
    assert product.name_en == 'iPhone'



# -------------- Delete ------------


@pytest.mark.django_db
def test_product_manager_can_delete_product(api_client,authenticate):
    """Users with delete_product can delete a product."""

    authenticate('delete_product')
    product = baker.make(models.Product)

    url = product_detail_url(product)
    response = api_client.delete(url,format='json')

    assert response.status_code == 204
    assert not models.Product.objects.filter(slug=product.slug).exists()


@pytest.mark.django_db
def test_anonymous_user_cannot_delete_product(api_client):
    """Unauthenticated users get 401 and the product still exists."""

    product = baker.make(models.Product)

    url = product_detail_url(product)
    response = api_client.delete(url,format='json')

    assert response.status_code == 401
    assert models.Product.objects.filter(slug=product.slug).exists()




    