from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Category(models.Model):

    # Category name fields for bilingual support
    name_en = models.CharField(max_length=100,db_index=True)
    name_ar = models.CharField(max_length=100,db_index=True)
    slug = models.SlugField(unique=True)

    # Return English name as the main string representation
    def __str__(self):
        return self.name_en

    # Generate a unique URL slug before saving the category
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name_en)
            self.slug = base
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base}-{counter}'
                counter += 1
        return super().save(*args, **kwargs)


class Product(models.Model):

    # Product database fields 

    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='products')
    slug = models.SlugField(unique=True)
    name_en = models.CharField(max_length=100, db_index=True)
    name_ar = models.CharField(max_length=100, db_index=True)
    brand = models.CharField(max_length=100, blank=True)
    description_en = models.TextField(max_length=500, blank=True)
    description_ar = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(validators=[MinValueValidator(0)], max_digits=7, decimal_places=2, db_index=True)

    # Return English name as the main string representation
    def __str__(self):
        return self.name_en

    # Generate a unique URL slug before saving the product
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name_en)
            self.slug = base
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base}-{counter}'
                counter += 1
        return super().save(*args, **kwargs)


class ProductImage(models.Model):

    # Manage product gallery images and visibility

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    img = models.ImageField(upload_to='',blank=True)
    title_en = models.CharField(max_length=100, blank=True)
    title_ar = models.CharField(max_length=100, blank=True)
    is_main = models.BooleanField(blank=True,null=True)

    # Return English title as the main string representation
    def __str__(self):
        return self.title_en