from django.urls import reverse


def get_detail_url(cart , cart_item):
    return reverse('cartitems-detail', kwargs={'cart_pk': cart.pk , 'pk': cart_item.pk})


def get_list_url(cart):
    return reverse('cartitems-list', kwargs={'cart_pk': cart.pk})


def get_data(product_id , **extra_fields):
    """A request body for adding a product; tests pass quantity only when they need it."""
    return {'product_id' : product_id} | extra_fields