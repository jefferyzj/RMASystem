from django.test import TestCase
from .models import Product, Category, Status, Task, Location

class ProductTestCase(TestCase):
    def setUp(self):
        # Create sample categories
        category1 = Category.objects.create(name="Category 1")
        category2 = Category.objects.create(name="Category 2")

        # Create sample statuses
        status1 = Status.objects.create(name="Status 1")
        status2 = Status.objects.create(name="Status 2")

        # Create sample tasks
        task1 = Task.objects.create(action="Task 1")
        task2 = Task.objects.create(action="Task 2")

        # Create sample locations
        location1 = Location.objects.create(rack_name="Rack 1", layer_number=1, space_number=1)
        location2 = Location.objects.create(rack_name="Rack 2", layer_number=2, space_number=2)

        # Create sample products
        Product.objects.create(
            SN="1234567890123",
            category=category1,
            priority_level="normal",
            description="Product 1 description",
            location=location1,
            short_12V_48V="P",
            current_status=status1,
            current_task=task1
        )
        Product.objects.create(
            SN="9876543210987",
            category=category2,
            priority_level="hot",
            description="Product 2 description",
            location=location2,
            short_12V_48V="F12",
            current_status=status2,
            current_task=task2
        )

    def test_display_all_products(self):
        products = Product.objects.all()
        for product in products:
            print(f"SN: {product.SN}, Category: {product.category.name}, Location: {product.location.rack_name}, Priority: {product.get_priority_level_display()}, Status: {product.current_status.name}, Task: {product.current_task.action}")

        self.assertEqual(products.count(), 2)