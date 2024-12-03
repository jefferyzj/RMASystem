import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            'SN': ['icontains'],
            'category__name': ['exact'],
            'location__rack_name': ['exact'],
            'priority_level': ['exact'],
            'current_status__name': ['exact'],
            'current_task__task_name': ['exact'],
        }