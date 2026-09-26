from django.contrib import admin
from . import models

@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    fields = ['user']

@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    fields = ['cart','product','quantity']

