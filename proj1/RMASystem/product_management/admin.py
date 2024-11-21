from django.contrib import admin
from .models import Category, Location, Status, Task, StatusTask, Product, ProductTask, ProductStatus

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('rack_name', 'layer_number', 'space_number')
    search_fields = ('rack_name', 'layer_number', 'space_number')
    list_filter = ('rack_name', 'layer_number', 'space_number')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_closed')
    search_fields = ('name', 'description')
    list_filter = ('is_closed',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('action', 'description', 'result', 'note')
    search_fields = ('action', 'description', 'result', 'note')

@admin.register(StatusTask)
class StatusTaskAdmin(admin.ModelAdmin):
    list_display = ('status', 'task', 'is_predefined', 'order')
    search_fields = ('status__name', 'task__action')
    list_filter = ('status', 'task', 'is_predefined')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('SN', 'category', 'priority_level', 'description', 'current_status', 'current_task', 'location', 'created', 'modified')
    search_fields = ('SN', 'category__name', 'description', 'current_status__name', 'current_task__action', 'location__rack_name')
    list_filter = ('category', 'priority_level', 'current_status', 'location')

@admin.register(ProductTask)
class ProductTaskAdmin(admin.ModelAdmin):
    list_display = ('product', 'task', 'is_completed', 'is_skipped', 'is_predefined', 'created', 'modified')
    search_fields = ('product__SN', 'task__action')
    list_filter = ('is_completed', 'is_skipped', 'is_predefined')

@admin.register(ProductStatus)
class ProductStatusAdmin(admin.ModelAdmin):
    list_display = ('product', 'status', 'changed_at')
    search_fields = ('product__SN', 'status__name')
    list_filter = ('status', 'changed_at')
