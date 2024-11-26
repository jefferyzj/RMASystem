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
    new_status_name = forms.CharField(max_length=100, required=False, label="Or Create New Status")
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects.all(), required=False, widget=forms.CheckboxSelectMultiple, label="Tasks")
    new_task_name = forms.CharField(max_length=100, required=False, label="Or Create New Task")

    class Meta:
        model = Product
        fields = ['SN', 'category', 'priority_level', 'description', 'current_status', 'new_status_name', 'tasks', 'new_task_name']
        widgets = {
            'SN': forms.TextInput(attrs={'readonly': 'readonly'}),
            'category': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_status'].queryset = Status.objects.all()
        self.fields['current_status'].help_text = "Select an existing status or enter a new one below"

    def clean(self):
        cleaned_data = super().clean()
        current_status = cleaned_data.get('current_status')
        new_status_name = cleaned_data.get('new_status_name')
        product = self.instance

        # Ensure either an existing status is selected or a new status is provided, but not both
        if not current_status and not new_status_name:
            raise forms.ValidationError("You must select an existing status or enter a new status.")
        if current_status and new_status_name:
            raise forms.ValidationError("You cannot select an existing status and enter a new status at the same time.")

        # Check if all required tasks are completed before changing the status
        if current_status != product.current_status:
            incomplete_tasks = product.tasks_of_product.filter(is_completed=False, is_skipped=False)
            if incomplete_tasks.exists():
                raise forms.ValidationError("All tasks must be completed or skipped before changing the status.")

        # Handle new status creation
        if new_status_name:
            if Status.objects.filter(name=new_status_name).exists():
                raise forms.ValidationError(f"Status with name '{new_status_name}' already exists.")
            new_status, created = Status.objects.get_or_create(name=new_status_name)
            cleaned_data['current_status'] = new_status

            # Create a new StatusTransition from the current status to the new status
            StatusTransition.objects.create(from_status=product.current_status, to_status=new_status)

            # Create a new ProductStatus
            ProductStatus.objects.create(product=product, status=new_status)

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        new_status_name = self.cleaned_data.get('new_status_name')
        tasks = self.cleaned_data.get('tasks')
        new_task_name = self.cleaned_data.get('new_task_name')

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
    

    new_status_name = forms.CharField(max_length=100, required=False, label="Or Create New Status")
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects.all(), required=False, widget=forms.CheckboxSelectMultiple, label="Tasks")
    new_task_name = forms.CharField(max_length=100, required=False, label="Or Create New Task")

    class Meta:
        model = Product
        fields = ['current_status', 'new_status_name', 'tasks', 'new_task_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_status'].queryset = Status.objects.all()
        self.fields['current_status'].help_text = "Select an existing status or enter a new one below"

    def clean(self):
        cleaned_data = super().clean()
        current_status = cleaned_data.get('current_status')
        new_status_name = cleaned_data.get('new_status_name')
        product = self.instance

        # Ensure either an existing status is selected or a new status is provided, but not both
        if not current_status and not new_status_name:
            raise forms.ValidationError("You must select an existing status or enter a new status.")
        if current_status and new_status_name:
            raise forms.ValidationError("You cannot select an existing status and enter a new status at the same time.")

        # Check if all required tasks are completed before changing the status
        if current_status != product.current_status:
            incomplete_tasks = product.tasks_of_product.filter(is_completed=False, is_skipped=False)
            if incomplete_tasks.exists():
                raise forms.ValidationError("All tasks must be completed or skipped before changing the status.")

        # Handle new status creation
        if new_status_name:
            if Status.objects.filter(name=new_status_name).exists():
                raise forms.ValidationError(f"Status with name '{new_status_name}' already exists.")
            new_status, created = Status.objects.get_or_create(name=new_status_name)
            cleaned_data['current_status'] = new_status

            # Create a new StatusTransition from the current status to the new status
            StatusTransition.objects.create(from_status=product.current_status, to_status=new_status)

            # Create a new ProductStatus
            ProductStatus.objects.create(product=product, status=new_status)

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        new_status_name = self.cleaned_data.get('new_status_name')
        tasks = self.cleaned_data.get('tasks')
        new_task_name = self.cleaned_data.get('new_task_name')

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