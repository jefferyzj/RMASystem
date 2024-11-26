from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Product, Category, Status, Task, ProductTask, StatusTask, Location, StatusTransition, ProductStatus

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
    class Meta:
        model = Location
        fields = ['rack_name', 'layer_number', 'space_number']

    def save(self, commit=True):
        location = super().save(commit=commit)
        if commit:
            num_layers = self.cleaned_data.get('num_layers')
            num_spaces_per_layer = self.cleaned_data.get('num_spaces_per_layer')
            if num_layers and num_spaces_per_layer:
                Location.create_rack_with_layers_and_spaces(location.rack_name, num_layers, num_spaces_per_layer)
        return location

class ProductForm(BaseForm):
    new_status_name = forms.CharField(max_length=100, required=False, label="Or Create New Status")
    possible_next_statuses = forms.ModelMultipleChoiceField(queryset=Status.objects.all(), required=False, label="Possible Next Statuses")

    class Meta:
        model = Product
        fields = ['SN', 'category', 'priority_level', 'description', 'current_status', 'current_task', 'location', 'new_status_name', 'possible_next_statuses']

    def clean(self):
        cleaned_data = super().clean()
        current_status = cleaned_data.get('current_status')
        new_status_name = cleaned_data.get('new_status_name')
        possible_next_statuses = cleaned_data.get('possible_next_statuses')
        product = self.instance

        # Check if all required tasks are completed before changing the status
        if current_status != product.current_status:
            incomplete_tasks = product.tasks_of_product.filter(is_completed=False, task__can_be_skipped=False)
            if incomplete_tasks.exists():
                raise forms.ValidationError(f"All required tasks must be completed or removed before changing the status -{current_status.name}-.")
        if new_status_name:
            if Status.objects.filter(name=new_status_name).exists():
                raise forms.ValidationError(f"Status with name -{new_status_name}- already exists.")
            new_status, created = Status.objects.get_or_create(name=new_status_name)
            cleaned_data['current_status'] = new_status
            cleaned_data['possible_next_statuses'] = possible_next_statuses

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        new_status_name = self.cleaned_data.get('new_status_name')
        possible_next_statuses = self.cleaned_data.get('possible_next_statuses')
        if commit:
            product.save()
            self.save_m2m()
            # Handle status transition
            if new_status_name:
                new_status = Status.objects.get(name=new_status_name)
                for next_status in possible_next_statuses:
                    StatusTransition.objects.get_or_create(from_status=new_status, to_status=next_status)
        return product

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