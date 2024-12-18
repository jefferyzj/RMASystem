from rest_framework import serializers
from .models import Category, Location, Status, StatusTransition, StatusTask, Task, ProductTask, ProductStatus, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    short_name = serializers.CharField(source='short_name', read_only=True)

    class Meta:
        model = Location
        fields = '__all__'

class StatusSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='get_product_count', read_only=True)
    task_count = serializers.IntegerField(source='get_task_count', read_only=True)

    class Meta:
        model = Status
        fields = '__all__'

class StatusTransitionSerializer(serializers.ModelSerializer):
    from_status_name = serializers.CharField(source='from_status.name', read_only=True)
    to_status_name = serializers.CharField(source='to_status.name', read_only=True)

    class Meta:
        model = StatusTransition
        fields = '__all__'

class StatusTaskSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = StatusTask
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class ProductTaskSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    product_sn = serializers.CharField(source='product.SN', read_only=True)

    class Meta:
        model = ProductTask
        fields = '__all__'

class ProductStatusSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='status.name', read_only=True)
    product_sn = serializers.CharField(source='product.SN', read_only=True)

    class Meta:
        model = ProductStatus
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    location_name = serializers.CharField(source='location.short_name', read_only=True)
    current_status_name = serializers.CharField(source='current_status.name', read_only=True)
    current_task_name = serializers.CharField(source='current_task.task_name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'