from django.contrib import admin
from posApp.models import Category, Product, Sales, SalesItem

# Register your models here.
admin.site.register(Category)
admin.site.register(Sales)
admin.site.register(SalesItem)
# admin.site.register(Employees)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'cost_price', 'quantity', 'store')
