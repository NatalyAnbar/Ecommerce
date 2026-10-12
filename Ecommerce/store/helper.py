from django.utils.text import slugify

def generate_unique_slug(instance,value):
    """Return a slug from `value` that no other object of the same model uses."""

    model = type(instance)
    base = slugify(value)
    slug = base
    counter = 1
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug