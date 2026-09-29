import pytest
from model_bakery import baker 
from store import models
from django.urls import reverse


def category_detail(category):
    """Return the detail endpoint URL for the given category (lookup by slug)."""

    return reverse('category-detail',args=[category.slug])


def valid_category_payload():
    """Return a valid request payload for creating or updating a category."""

    return {'name_en':'Electronics',
            'name_ar':'الكترونيات'}


# ============================================================
# Read: public access
# ============================================================

@pytest.mark.django_db
def test_anyone_can_list_categories(api_client):
    """Anonymous users can retrieve the category list."""

    categories = baker.make(models.Category,_quantity=5)
    
    url = reverse('category-list')
    response = api_client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_anyone_can_retrieve_category_by_slug(api_client):
    """Anonymous users can retrieve a single category by its slug."""

    category = baker.make(models.Category)

    url = category_detail(category)
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['slug'] == category.slug


# ============================================================
# Create
# ============================================================

@pytest.mark.django_db
def test_anonymous_user_cannot_create_category(api_client):
    """Unauthenticated users are rejected when creating a category."""

    url = reverse('category-list')
    data = valid_category_payload()
    respone = api_client.post(url, data, format='json')

    assert respone.status_code in [401,403]


@pytest.mark.django_db
def test_user_with_add_permission_can_create_category(api_client,authenticate):
    """Users with 'add_category' permission can create a category."""

    authenticate('add_category')

    url = reverse('category-list')
    data = valid_category_payload()
    response = api_client.post(url, data, format='json')

    assert response.status_code == 201
    assert models.Category.objects.filter(id=response.data['id']).exists()


# ============================================================
# Update
# ============================================================

@pytest.mark.django_db
def test_user_with_change_permission_can_update_category(api_client,authenticate):
    """PUT with all fields replaces both translated names."""

    authenticate('change_category')
    category = baker.make(models.Category, name_en='Old', name_ar='قديم')

    url = category_detail(category)
    data = valid_category_payload()
    response = api_client.put(url ,data ,format='json')

    assert response.status_code == 200
    category.refresh_from_db()
    assert category.name_en == 'Electronics'
    assert category.name_ar == 'الكترونيات'


@pytest.mark.django_db
def test_anonymous_user_cannot_update_category(api_client):
    """Unauthenticated users are rejected when updating a category."""

    category = baker.make(models.Category,name_en = 'old', name_ar = 'قديم')

    url = category_detail(category)
    data = valid_category_payload()
    response = api_client.put(url,data,format='json')

    assert response.status_code == 401


# ============================================================
# Delete
# ============================================================

@pytest.mark.django_db
def test_user_with_delete_permission_can_delete_category(api_client,authenticate):
    """Users with 'delete_category' permission can delete a category."""

    authenticate('delete_category')
    category = baker.make(models.Category)

    url = category_detail(category)
    response = api_client.delete(url,{},format='json')

    assert response.status_code == 204
    assert not models.Category.objects.filter(id=category.id).exists()


def test_anonymous_user_cannot_delete_category(api_client):
    """Unauthenticated users are rejected when deleting a category."""

    category = baker.make(models.Category)

    url = category_detail(category)
    response = api_client.delete(url,{},format='json')

    assert response.status_code in [401,403]



