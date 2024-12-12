import django_filters
from django import forms
from .models import Product, Category, Status, Task, Location
from .utilhelpers import PRIORITY_LEVEL_CHOICES

class ProductFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name='name',
        label='Category',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = django_filters.CharFilter(field_name='SN', lookup_expr='icontains', label='Search by SN')
    location = django_filters.ChoiceFilter(label='Location', method='filter_by_location')
    priority_level = django_filters.ChoiceFilter(choices=PRIORITY_LEVEL_CHOICES, label='Priority Level')
    current_status = django_filters.ModelChoiceFilter(queryset=Status.objects.all(), to_field_name='name', label='Current Status')
    current_task = django_filters.ModelChoiceFilter(queryset=Task.objects.all(), to_field_name='task_name', label='Current Task')

    class Meta:
        model = Product
        fields = ['category', 'search', 'location', 'priority_level', 'current_status', 'current_task']

    def filter_by_location(self, queryset, name, value):
        if value:
            rack_name, layer_number = value.split('L')
            return queryset.filter(location__rack_name=rack_name, location__layer_number=layer_number)
        return queryset

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct()

    @property
    def location_choices(self):
        locations = Location.objects.values('rack_name', 'layer_number').distinct()
        choices = [(f"{loc['rack_name']}L{loc['layer_number']}", f"R{loc['rack_name']}L{loc['layer_number']}") for loc in locations]
        return choices

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['location'].extra['choices'] = self.location_choices
        # Set the default category to "PG520"
        self.filters['category'].field.initial = Category.objects.get(name="PG520")