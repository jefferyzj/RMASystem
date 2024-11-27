from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Product, Category, Status, Task, ProductTask, StatusTask, Location, StatusTransition, ProductStatus
from django.db import transaction
from .utilhelpers import PRIORITY_LEVEL_CHOICES

class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class CategoryForm(BaseForm):
    class Meta:
        model = Category
        fields = ['name']

class StatusForm(BaseForm):
    class Meta:
        model = Status
        fields = ['name', 'description', 'is_closed']

class TaskForm(BaseForm):
    class Meta:
        model = Task
        fields = ['action', 'description']

class ProductTaskForm(BaseForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'result', 'note', 'is_completed', 'is_skipped', 'is_predefined']

class StatusTaskForm(BaseForm):
    class Meta:
        model = StatusTask
        fields = ['status', 'task', 'is_predefined']

class LocationForm(BaseForm):
    num_layers = forms.IntegerField(required=False, label="Number of Layers")
    num_spaces_per_layer = forms.IntegerField(required=False, label="Number of Spaces per Layer")

    class Meta:
        model = Location
        fields = ['rack_name', 'layer_number', 'space_number', 'num_layers', 'num_spaces_per_layer']

    def save(self, commit=True):
        location = super().save(commit=commit)
        if commit:
            num_layers = self.cleaned_data.get('num_layers')
            num_spaces_per_layer = self.cleaned_data.get('num_spaces_per_layer')
            if num_layers and num_spaces_per_layer:
                Location.create_rack_with_layers_and_spaces(location.rack_name, num_layers, num_spaces_per_layer)
        return location

class StatusTransitionForm(forms.ModelForm):
    new_status_name = forms.CharField(max_length=100, required=False, label="Or Create New Status")

    class Meta:
        model = StatusTransition
        fields = ['from_status', 'to_status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super().clean()
        new_status_name = cleaned_data.get('new_status_name')
        to_status = cleaned_data.get('to_status')

        if not to_status and not new_status_name:
            raise forms.ValidationError("You must choose an existing status or create a new one.")

        if new_status_name:
            new_status, created = Status.objects.get_or_create(name=new_status_name)
            cleaned_data['to_status'] = new_status

        return cleaned_data

class ProductStatusForm(forms.ModelForm):
    class Meta:
        model = ProductStatus
        fields = ['product', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class ProductForm(BaseForm):
    next_status_select = forms.ModelChoiceField(queryset=Status.objects.none(), required=False, label="Next Status")
    next_status_enter = forms.CharField(max_length=100, required=False, label="Or Create New Status")
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects.all(), required=False, widget=forms.CheckboxSelectMultiple, label="Tasks")
    new_task_name = forms.CharField(max_length=100, required=False, label="Or Create New Task")
    new_location = forms.CharField(max_length=100, required=False, label="Or Create New Location")

    class Meta:
        model = Product
        fields = ['SN', 'category', 'priority_level', 'description', 'current_status', 'current_task', 'short_12V_48V', 'next_status_select', 'next_status_enter', 'tasks', 'new_task_name', 'location', 'new_location']
        widgets = {
            'SN': forms.TextInput(attrs={'readonly': 'readonly'}),
            'category': forms.TextInput(attrs={'readonly': 'readonly'}),
            'priority_level': forms.Select(choices=PRIORITY_LEVEL_CHOICES),
            'description': forms.Textarea(attrs={'rows': 3}),
            'location': forms.Select(),
            'short_12V_48V': forms.Select(choices=[('P', 'Pass'), ('F12', 'Fail on 12V'), ('F48', 'Fail on 48V')]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product = kwargs.get('instance')
        # queryset is the dropdown list of possible next statuses of the current.status.
        if product and product.current_status:
            self.fields['next_status_select'].queryset = product.current_status.get_possible_next_statuses()
        else:
            self.fields['next_status_select'].queryset = Status.objects.none()
        self.fields['next_status_select'].help_text = "Select an existing status or enter a new one below"
        self.fields['location'].queryset = Location.objects.filter(products__isnull=True)

    def clean(self):
        cleaned_data = super().clean()
        next_status_select = cleaned_data.get('next_status_select')
        next_status_enter = cleaned_data.get('next_status_enter')
        new_location_name = cleaned_data.get('new_location')
        product = self.instance

        # Ensure either an existing status is selected or a new status is provided, but not both
        if not next_status_select and not next_status_enter:
            raise forms.ValidationError("You must select an existing status or enter a new status.")
        if next_status_select and next_status_enter:
            raise forms.ValidationError("You cannot select an existing status and enter a new status at the same time.")

        # Handle new status creation
        if next_status_enter:
            if Status.objects.filter(name=next_status_enter).exists():
                raise forms.ValidationError(f"Status with name '{next_status_enter}' already exists.")
            new_status, created = Status.objects.get_or_create(name=next_status_enter)
            # in this case, we also set the selected status to the new status, and operate it on save() method
            cleaned_data['next_status_select'] = new_status

            # Create a new StatusTransition from the current status to the new status
            if product.current_status:
                StatusTransition.objects.create(from_status=product.current_status, to_status=new_status)

            # Create a new ProductStatus
            ProductStatus.objects.create(product=product, status=new_status)

        # Handle new location creation
        if new_location_name:
            new_location, created = Location.objects.get_or_create(rack_name=new_location_name)
            cleaned_data['location'] = new_location

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        product = super().save(commit=False)
        next_status_select = self.cleaned_data.get('next_status_select')
        tasks = self.cleaned_data.get('tasks')
        new_task_name = self.cleaned_data.get('new_task_name')
        new_location = self.cleaned_data.get('new_location')

        # Update the product's current status to the selected or newly created status
        if next_status_select:
            product.current_status = next_status_select

        # Update the product's location to the newly created location if provided
        if new_location:
            product.location = new_location

        if commit:
            product.save()
            self.save_m2m()

            # Handle tasks assignment
            if tasks or new_task_name:
                # Clear existing tasks
                ProductTask.objects.filter(product=product).delete()

                # Assign new tasks
                if tasks:
                    for task in tasks:
                        # Create or get StatusTask for the current status and task
                        StatusTask.objects.get_or_create(status=product.current_status, task=task)
                        ProductTask.objects.create(product=product, task=task)

                # Handle new task creation
                if new_task_name:
                    new_task, created = Task.objects.get_or_create(action=new_task_name)
                    # Create or get StatusTask for the current status and new task
                    StatusTask.objects.get_or_create(status=product.current_status, task=new_task)
                    ProductTask.objects.create(product=product, task=new_task)

        return product