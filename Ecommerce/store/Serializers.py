from rest_framework import serializers
from Ecommerce.mixins import TranslationMixin
from . import models

class ImageSerializer(TranslationMixin, serializers.ModelSerializer):

    # Dynamically fetch image title based on client active language
    title = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductImage
        fields = ['id','product','img','title','is_main']

    # Resolve localization using global translation mixin
    def get_title(self,obj):
        return self.resolve_translated_value(obj,'title')


class ProductSerializer(TranslationMixin, serializers.ModelSerializer):

    # Handle product details with nested images 
    images = ImageSerializer(read_only=True, many=True)
    uploaded_img = serializers.ListField(
            child = serializers.ImageField(
                allow_empty_file=False),
                write_only = True)
    
    slug = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    # Write-only fields to store multilingual translations into the database
    name_en = serializers.CharField(write_only=True)
    name_ar = serializers.CharField(write_only=True)
    description_en = serializers.CharField(write_only=True)
    description_ar = serializers.CharField(write_only=True)

    class Meta:
        model = models.Product
        fields = ['id','category','slug','brand','price','name','description',
                  'uploaded_img','images','name_en', 'name_ar', 'description_en', 
                  'description_ar']

    def create(self, validated_data):

        # Extract uploaded images and save the new product instance
        images = validated_data.pop('uploaded_img')
        product = models.Product.objects.create(**validated_data)

        # Save multiple product gallery images sequentially
        for img in images:
            models.ProductImage.objects.create(product=product,img=img)

        return product

    # Resolve product name dynamically based on language
    def get_name(self,obj):
        return self.resolve_translated_value(obj,'name')

    # Resolve product description dynamically based on language
    def get_description(self,obj):
        return self.resolve_translated_value(obj,'description')


class CategorySerializer(TranslationMixin, serializers.ModelSerializer):
    products = ProductSerializer(many=True,read_only=True)
    slug = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.Category
        fields = ['id','name','slug','products']

    # Resolve category name dynamically based on language
    def get_name(self,obj):
        return self.resolve_translated_value(obj,'name')





