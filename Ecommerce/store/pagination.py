from rest_framework.pagination import PageNumberPagination

class DefaultPagination(PageNumberPagination):
    """
    Page-number pagination with a client-adjustable page size.

    Clients may request a custom size with `?page_size=N`, capped at
    `max_page_size` to protect the server from oversized responses.

    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 30