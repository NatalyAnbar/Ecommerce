
"""Serializers for the store API: products, categories, images and reviews."""

from django.db import transaction
from rest_framework import serializers
from Ecommerce.mixins import TranslationMixin
from . import models, store_validators


class MiniReviewSeializer(serializers.ModelSerializer):
    """The public face of a user, shown next to their reviews; never add private fields here."""
    class Meta:
        model = models.User
        fields = ['first_name']


class ReviewSerializer(serializers.ModelSerializer):
    """A product review; the author and product are set by the view, never by the client."""

    # Shown as a small object so more public fields (like a photo) can be added later
    # without changing the response's shape
    user = MinieviewSeializer(read_only=True)
    class Meta:
        model = models.Review
        fields = ['id', 'rating', 'comment', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


    def validate(self, attrs):
        """Reject a second review of the same product, returning 400 instead of a database error."""
        user = self.context['request'].user
        product_slug = self.context['product_slug']

        # Only on create: editing your own review must stay possible
        is_new_review = self.instance is None

        if is_new_review and models.Review.objects.filter(
                    user=user, product__slug=product_slug
                ).exists():
            raise serializers.ValidationError('You have already reviewed this product.')
        
        return attrs


class ImageSerializer(TranslationMixin, serializers.ModelSerializer):
    """A product gallery image. Format and size rules come from the model field."""

    # Title in the client's language (Accept-Language)
    title = serializers.SerializerMethodField()
    title_en = serializers.CharField(write_only=True)
    title_ar = serializers.CharField(write_only=True)

    class Meta:
        model = models.ProductImage
        fields = ['id', 'img', 'title_en' ,'title_ar', 'title', 'is_main']

    def get_title(self, obj):
        return self.resolve_translated_value(obj, 'title')


class ProductSerializer(TranslationMixin, serializers.ModelSerializer):
    """
    A product with its gallery.

    Images are read through `images` and uploaded through `uploaded_img`
    (on create, or on update to add more).
    """

    images = ImageSerializer(read_only=True, many=True)
    uploaded_img = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            validators=store_validators.PRODUCT_IMAGE_VALIDATORS,
        ),
        write_only=True,
        required=False,
    )

    slug = serializers.CharField(read_only=True)

    # Name and description in the client's language (read)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    # Both translations, stored in the database (write)
    name_en = serializers.CharField(write_only=True)
    name_ar = serializers.CharField(write_only=True)
    description_en = serializers.CharField(write_only=True)
    description_ar = serializers.CharField(write_only=True)

    # Computed in the view's queryset with annotate()
    avg_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Product
        fields = [
            'id', 'category', 'slug', 'brand', 'price',
            'name', 'name_en', 'name_ar',
            'description', 'description_en', 'description_ar',
            'uploaded_img', 'images',
            'avg_rating', 'reviews_count',
        ]

    def validate_uploaded_img(self, new_images):
        """Keep the product's total number of images within the limit."""
        # New products start with no images; existing ones keep theirs
        existing_count = self.instance.images.count() if self.instance else 0
        store_validators.validate_image_limit(existing_count, len(new_images))
        return new_images

    def create(self, validated_data):
        images = validated_data.pop('uploaded_img', [])
        # Product and images are saved together: if an image fails, nothing is saved
        with transaction.atomic():
            product = super().create(validated_data)
            self._add_images(product, images)
        return product

    def update(self, instance, validated_data):
        images = validated_data.pop('uploaded_img', [])
        # Uploaded images are added to the existing ones, not replacing them
        with transaction.atomic():
            product = super().update(instance, validated_data)
            self._add_images(product, images)
        return product

    def _add_images(self, product, images):
        """Attach uploaded images to the product; the first one becomes main if it has none."""
        has_main_image = product.images.filter(is_main=True).exists()
        for index, img in enumerate(images):
            models.ProductImage.objects.create(
                product=product,
                img=img,
                is_main=(not has_main_image and index == 0),
            )

    def get_name(self, obj):
        return self.resolve_translated_value(obj, 'name')

    def get_description(self, obj):
        return self.resolve_translated_value(obj, 'description')


class CategorySerializer(TranslationMixin, serializers.ModelSerializer):
    """A category with its products."""

    products = ProductSerializer(many=True, read_only=True)
    slug = serializers.CharField(read_only=True)

    # Name in the client's language (read) and both translations (write)
    name = serializers.SerializerMethodField()
    name_en = serializers.CharField(write_only=True)
    name_ar = serializers.CharField(write_only=True)

    class Meta:
        model = models.Category
        fields = ['id', 'name_en', 'name_ar', 'name', 'slug', 'products']

    def get_name(self, obj):
        return self.resolve_translated_value(obj, 'name')