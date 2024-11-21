from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Product, Category, Status, Task, ProductTask, StatusTask, Location, StatusTransition, ProductStatus

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['name', 'description', 'is_closed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

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

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['action', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class ProductTaskForm(forms.ModelForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'result', 'note','is_completed', 'is_skipped', 'is_predefined']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class StatusTaskForm(forms.ModelForm):
    class Meta:
        model = StatusTask
        fields = ['status', 'task', 'is_predefined']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class ProductForm(forms.ModelForm):
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'priority_level', 'description', 'current_status', 'current_task', 'location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super().clean()
        current_status = cleaned_data.get('current_status')
        product = self.instance

        # Check if all required tasks are completed before changing the status
        if current_status != product.current_status:
            incomplete_tasks = product.tasks_of_product.filter(is_completed=False, task__can_be_skipped=False)
            if incomplete_tasks.exists():
                raise forms.ValidationError("All required tasks must be completed or removed before changing the status.")

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        if commit:
            product.save()
            self.save_m2m()
        return product

class LocationForm(forms.ModelForm):
    num_layers = forms.IntegerField(required=False, min_value=1, label="Number of Layers")
    num_spaces_per_layer = forms.IntegerField(required=False, min_value=1, label="Number of Spaces per Layer")

    class Meta:
        model = Location
        fields = ['rack_name', 'layer_number', 'space_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

    def save(self, commit=True):
        location = super().save(commit=commit)
        if commit:
            num_layers = self.cleaned_data.get('num_layers')
            num_spaces_per_layer = self.cleaned_data.get('num_spaces_per_layer')
            if num_layers and num_spaces_per_layer:
                Location.create_rack_with_layers_and_spaces(location.rack_name, num_layers, num_spaces_per_layer)
        return location

class ProductStatusForm(forms.ModelForm):
    class Meta:
        model = ProductStatus
        fields = ['product', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))