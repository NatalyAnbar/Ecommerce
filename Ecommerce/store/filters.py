import django_filters
from . import models

class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__slug')
    price_min = django_filters.NumberFilter(field_name='price' , lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price' , lookup_expr='lte')

    class Meta:
        model = models.Product
        fields = ['price_min','price_max','brand','category']