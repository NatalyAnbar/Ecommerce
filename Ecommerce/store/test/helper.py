from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from django.urls import reverse
import math
import os


"""Shared helpers for tests."""


def make_image(width=700, height=700, name='test', extension='png', size_mb=None):
    """
    Return an in-memory image that can be uploaded like a real file.

    The default size and extension pass the product image rules; change them
    to test rejected uploads. Pass `size_mb` to get a square image of at least
    that many megabytes (width and height are then ignored); keep the default
    PNG extension for this, since JPEG would compress the file below that size.
    """
    if size_mb:
        # Random pixels can't be compressed, so the file is about 3 bytes per pixel
        side = math.ceil(math.sqrt(size_mb * 1024 * 1024 / 3))
        image = Image.frombytes('RGB', (side, side), os.urandom(side * side * 3))
    else:
        image = Image.new('RGB', (width, height), color='red')

    # Pillow and MIME types call .jpg "JPEG"; other extensions match their format name
    image_format = 'jpeg' if extension == 'jpg' else extension

    buffer = BytesIO()
    image.save(buffer, image_format.upper())
    return SimpleUploadedFile(
        f'{name}.{extension}',
        buffer.getvalue(),
        content_type=f'image/{image_format}',
    )

def get_payload(category, **kwargs):
    """Valid data for creating a product. Pass keyword arguments to change any field."""
    return {
        'category' : category.id,
        'price' : 100,
        'name_en' : 'iphone',
        'name_ar' : 'ايفون',
        'description_en' : 'A good phone',
        'description_ar' : 'هاتف جيد',   
    } | kwargs


def product_list_url():
    """URL for listing and creating products."""
    return reverse('product-list')