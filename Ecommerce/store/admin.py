from django.contrib import admin
from . import models

admin.site.site_header = 'Admin Panel'

@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name_en','name_ar']
    list_filter = ['name_en','name_ar']
    search_fields = ['name_en','name_ar']
    prepopulated_fields = {'slug':['name_en']}


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name_en','name_ar','brand','price']
    list_filter = ['name_en','name_ar','brand']
    search_fields = ['name_en','name_ar','brand']
    prepopulated_fields = {'slug' : ['name_en']}


@admin.register(models.ProductImage)
class ImageAdmin(admin.ModelAdmin):
    fields = ['title_en','title_ar']   


