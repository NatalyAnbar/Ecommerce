from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.validators import FileExtensionValidator

# SVG is excluded on purpose: it can contain scripts (XSS risk)
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
MAX_IMAGE_FILE_SIZE_MB = 5
MIN_IMAGE_DIMENSIONS = (500, 500)
MAX_IMAGE_DIMENSIONS = (5000, 5000)
MAX_IMAGES_PER_PRODUCT = 8
MAX_ASPECT_RATIO = 2  # width/height (or height/width) can't exceed 2:1

validate_image_extension = FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)

def validate_image_file_size(image):
    """Reject files larger than MAX_IMAGE_FILE_SIZE_MB."""

    if image.size > MAX_IMAGE_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'Image file must be {MAX_IMAGE_FILE_SIZE_MB} MB or smaller.')


def validate_image_dimensions(image):
    """Reject images outside MIN_IMAGE_DIMENSIONS and MAX_IMAGE_DIMENSIONS (in pixels)."""

    width,height = get_image_dimensions(image)
    min_width, min_height = MIN_IMAGE_DIMENSIONS
    max_width, max_height = MAX_IMAGE_DIMENSIONS

    if width < min_width or height < min_height:
        raise ValidationError(f'Image must be at least {min_width}×{min_height} pixels.')
    if width > max_width or height > max_height:
        raise ValidationError(f'Image must be at most {max_width}×{max_height} pixels.')


def validate_image_aspect_ratio(image):
    """Reject images that are too wide or too tall (beyond MAX_ASPECT_RATIO:1)."""

    width,height = get_image_dimensions(image)
    ratio = max(width , height) / min(width , height)

    if ratio > MAX_ASPECT_RATIO :
        raise ValidationError(f'Image proportions must not exceed {MAX_ASPECT_RATIO}:1.')


def validate_image_limit(existing_count , new_count):
    if existing_count + new_count > MAX_IMAGES_PER_PRODUCT :
        raise ValidationError(f'A product can have at most {MAX_IMAGES_PER_PRODUCT} images.')


PRODUCT_IMAGE_VALIDATORS = [
    validate_image_extension,
    validate_image_file_size,
    validate_image_dimensions,
    validate_image_aspect_ratio
]