
"""Store models: categories, products, their images and customer reviews."""

from django.db import models
from django.contrib.auth import get_user_model
from django.core import validators
from . import store_validators,helper

User = get_user_model()

class Category(models.Model):
    """A product category, with names in English and Arabic."""

    name_en = models.CharField(max_length=100,db_index=True)
    name_ar = models.CharField(max_length=100,db_index=True)
    slug = models.SlugField(unique=True)

    class Meta:
        # A fixed order keeps paginated results stable
        ordering = ['slug']

    def __str__(self):
        return self.name_en

    def save(self, *args, **kwargs):
        """Generate a unique slug from the English name on first save."""

        if not self.slug:
            self.slug = helper.generate_unique_slug(self,self.name_en)
        return super().save(*args, **kwargs)


class Product(models.Model):
    """A product for sale, with bilingual name and description."""

    # Products stay in the store if their category is deleted
    category = models.ForeignKey('Category', 
                                 on_delete=models.SET_NULL, 
                                 null=True, 
                                 related_name='products')
    slug = models.SlugField(unique=True)
    name_en = models.CharField(max_length=100, db_index=True)
    name_ar = models.CharField(max_length=100, db_index=True)
    brand = models.CharField(max_length=100, blank=True, db_index=True)
    description_en = models.TextField(max_length=500, blank=True)
    description_ar = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(validators=[validators.MinValueValidator(0)], 
                                max_digits=7, 
                                decimal_places=2, 
                                db_index=True)
    # How many units are available to sell.
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        # A fixed order keeps paginated results stable
        ordering = ['slug']

    def __str__(self):
        return self.name_en


    def save(self, *args, **kwargs):
        """Generate a unique slug from the English name on first save."""

        if not self.slug:
            self.slug = helper.generate_unique_slug(self, self.name_en)
        return super().save(*args, **kwargs)


class ProductImage(models.Model):
    """A gallery image of a product. One image per product can be marked as main."""

    product = models.ForeignKey('Product', 
                                on_delete=models.CASCADE, 
                                related_name='images')

    # Format, file size and dimensions are checked by store_validators
    img = models.ImageField(upload_to='products/' , 
                            validators=store_validators.PRODUCT_IMAGE_VALIDATORS)
    
    title_en = models.CharField(max_length=100, blank=True)
    title_ar = models.CharField(max_length=100, blank=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ['title_en']

    def __str__(self):
        return self.title_en or f'Image {self.pk} of {self.product}'


class Review(models.Model):
    """A customer's 1_5 star rating of a product, with an optional comment."""

    rating = models.PositiveIntegerField(validators=[validators.MinValueValidator(1),
                                                     validators.MaxValueValidator(5)])

    comment = models.TextField(max_length=500,blank=True)
 
    # Keep the review if the author deletes their account, so the product's rating history stays intact
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL,
                             null=True,
                             related_name='user_reviews')

    # A review has no meaning without its product
    product = models.ForeignKey('Product',
                                on_delete=models.CASCADE,
                                related_name='product_reviews')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

        # Each user may review a given product only once
        constraints = [
            models.UniqueConstraint(
                fields=['user','product'] , name='user_product_review'
                )
        ]

    def __str__(self):
        return f'{self.rating}★ on {self.product} by {self.user or "deleted user"}'