import pytest
from model_bakery import baker 
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.contrib.auth.models import Group


User = get_user_model()

@pytest.mark.django_db
def test_product_managers_role_has_expected_permissions():

    """The Product Managers group grants catalog management except deleting categories."""

    call_command('setup_roles')
    user = baker.make(User)
    group = Group.objects.get(name = 'Product Managers')
    user.groups.add(group)

    assert user.has_perm('store.add_product')
    assert user.has_perm('store.change_product')
    assert user.has_perm('store.delete_product')
    assert user.has_perm('store.add_productimage')
    assert user.has_perm('store.change_category')
    assert not user.has_perm('store.delete_category')

    

@pytest.mark.django_db
def test_regular_user_has_no_catalog_permissions():

    """A user outside any staff group cannot manage the catalog."""
    
    user = baker.make(User)

    assert not user.has_perm('store.add_category')
    assert not user.has_perm('store.change_category')
    assert not user.has_perm('store.add_product')