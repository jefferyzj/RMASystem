from django.contrib import admin
from .models import Product, Category, Status, Task, ProductTask, StatusTask, Location, StatusTransition, ProductStatus

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('rack_name', 'layer_number', 'space_number', 'product')
    search_fields = ('rack_name',)
    list_filter = ('rack_name', 'layer_number', 'space_number')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_closed')
    search_fields = ('name', 'description')
    list_filter = ('is_closed',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('action', 'description')
    search_fields = ('action', 'description')

@admin.register(StatusTask)
class StatusTaskAdmin(admin.ModelAdmin):
    list_display = ('status', 'task', 'is_predefined', 'order')
    search_fields = ('status__name', 'task__action')
    list_filter = ('is_predefined', 'status')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('SN', 'category', 'priority_level', 'current_status', 'current_task', 'location')
    search_fields = ('SN', 'category__name', 'current_status__name', 'current_task__action', 'location__rack_name')
    list_filter = ('priority_level', 'current_status', 'location')

@admin.register(ProductTask)
class ProductTaskAdmin(admin.ModelAdmin):
    list_display = ('product', 'task', 'is_completed', 'is_skipped', 'is_predefined')
    search_fields = ('product__SN', 'task__action')
    list_filter = ('is_completed', 'is_skipped', 'is_predefined')

@admin.register(ProductStatus)
class ProductStatusAdmin(admin.ModelAdmin):
    list_display = ('product', 'status', 'changed_at')
    search_fields = ('product__SN', 'status__name')
    list_filter = ('status', 'changed_at')

@admin.register(StatusTransition)
class StatusTransitionAdmin(admin.ModelAdmin):
    list_display = ('from_status', 'to_status')
    search_fields = ('from_status__name', 'to_status__name')
