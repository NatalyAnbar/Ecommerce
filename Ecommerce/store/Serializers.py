from rest_framework import serializers
from Ecommerce.mixins import TranslationMixin
from . import models

class ImageSerializer(TranslationMixin, serializers.ModelSerializer):
    """Serialize product images with a title localized to the request language."""

    title = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductImage
        fields = ['id','product','img',
                  'title','is_main']

    def get_title(self,obj):
        """Return the image title in the client's active language."""

        return self.resolve_translated_value(obj,'title')


class ProductSerializer(TranslationMixin, serializers.ModelSerializer):
    """
    Serialize products with localized name/description and nested images.

    - Read: returns `name` and `description` in the active language.
    - Write: accepts both translations (`*_en`, `*_ar`) and an optional
      list of images via `uploaded_img`.
    """
    
    images = ImageSerializer(read_only=True, many=True)
    uploaded_img = serializers.ListField(
            child = serializers.ImageField(
                allow_empty_file=False),
                write_only = True)
    
    slug = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    # Translation inputs (write-only); the localized values are exposed via `name`/`description`
    name_en = serializers.CharField(write_only=True)
    name_ar = serializers.CharField(write_only=True)
    description_en = serializers.CharField(write_only=True)
    description_ar = serializers.CharField(write_only=True)

    class Meta:
        model = models.Product
        fields = ['id','category','slug',
                  'brand','price',
                  'name','name_en','name_ar',
                  'description','description_en','description_ar',
                  'uploaded_img','images']

    def create(self, validated_data):
        """Create the product, then attach any uploaded gallery images."""

        images = validated_data.pop('uploaded_img')
        product = models.Product.objects.create(**validated_data)

        for img in images:
            models.ProductImage.objects.create(product=product,img=img)
        return product


    def get_name(self,obj):
        """Return the product name in the client's active language."""

        return self.resolve_translated_value(obj,'name')


    def get_description(self,obj):
        """Return the product description in the client's active language."""

        return self.resolve_translated_value(obj,'description')


class CategorySerializer(TranslationMixin, serializers.ModelSerializer):
    """
    Serialize categories with a localized name and their nested products.

    The slug is generated automatically from `name_en` and is read-only.
    """

    products = ProductSerializer(many=True,read_only=True)
    slug = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()

    # Translation inputs (write-only); the localized value is exposed via `name`
    name_en = serializers.CharField(write_only=True)
    name_ar = serializers.CharField(write_only=True)

    class Meta:
        model = models.Category
        fields = ['id','name_en','name_ar',
                  'name','slug','products']

    def get_name(self,obj):
        """Return the category name in the client's active language."""
        
        return self.resolve_translated_value(obj,'name')





