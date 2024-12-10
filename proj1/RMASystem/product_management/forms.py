from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Product, Category, Status, Task, ProductTask, StatusTask, Location, StatusTransition, ProductStatus
from django.db import transaction
from .utilhelpers import PRIORITY_LEVEL_CHOICES
from django.core.validators import RegexValidator, MinValueValidator
from django.forms import modelformset_factory


class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class CategoryForm(BaseForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label="Select Category to Delete")

    class Meta:
        model = Category
        fields = ['name', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        product_count = obj.products.count()
        return f"{obj.name} ({product_count} products)"
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Ensure the category name is unique
        if Category.objects.filter(name=name).exists():
            raise forms.ValidationError(f'A category with the name "{name}" already exists.')
        return name

class StatusForm(BaseForm):
    possible_next_statuses = forms.ModelMultipleChoiceField(
        queryset=Status.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Possible Next Statuses",
    )

    class Meta:
        model = Status
        fields = ['name', 'description', 'is_closed', 'possible_next_statuses']

    def save(self, commit=True):
        status = super().save(commit=False)
        if commit:
            status.save()
            self.save_m2m()
            possible_next_statuses = self.cleaned_data.get('possible_next_statuses')
            if possible_next_statuses:
                for next_status in possible_next_statuses:
                    StatusTransition.objects.get_or_create(from_status=status, to_status=next_status)
                    print("StatusTransition created")
        return status

class TaskForm(BaseForm):
    task_name = forms.CharField(max_length=100, label="Task Name")
    description = forms.CharField(widget=forms.Textarea, required=False, label="Description")

    class Meta:
        model = Task
        fields = ['task_name', 'description']

    @transaction.atomic
    def save(self, commit=True):
        task = super().save(commit=False)
        if commit:
            task.save()
        return task


class StatusTaskForm(forms.ModelForm):
    status = forms.ModelChoiceField(queryset=Status.get_existing_statuses(), required=True, label="Map to Status")
    task = forms.ModelChoiceField(queryset=Task.objects.all(), required=True, label="Select Task")
    is_predefined = forms.BooleanField(required=False, label="Set as Predefined Task", initial=False)
    order = forms.ChoiceField(required=False, label="Order")
    existing_tasks = forms.ChoiceField(required=False, label="Select Task to Delete")

    class Meta:
        model = StatusTask
        fields = ['status', 'task', 'is_predefined', 'order', 'existing_tasks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'status' in self.data:
            try:
                status_id = int(self.data.get('status'))
                predefined_tasks = StatusTask.objects.filter(status_id=status_id, is_predefined=True).order_by('order')
                self.fields['order'].choices = [(i, i) for i in range(1, predefined_tasks.count() + 2)]
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            predefined_tasks = StatusTask.objects.filter(status=self.instance.status, is_predefined=True).order_by('order')
            self.fields['order'].choices = [(i, i) for i in range(1, predefined_tasks.count() + 2)]

        # Customize the choices for existing tasks to include status and predefined information
        self.fields['existing_tasks'].choices = StatusTask.get_existing_tasks_choices()

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        is_predefined = cleaned_data.get('is_predefined', False)  # Default to False if not provided
        order = cleaned_data.get('order')

        if is_predefined:
            if not status or order is None:
                raise forms.ValidationError("You must specify a status and an order for the predefined task.")
        else:
            cleaned_data['order'] = None  # Set order to None if is_predefined is False

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        status_task = super().save(commit=False)
        if commit:
            status_task.save()
        return status_task

class ProductTaskForm(BaseForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'result', 'note', 'is_completed', 'is_skipped', 'is_predefined']


from django import forms
from django.core.validators import MinValueValidator
from .models import Location

class LocationForm(forms.ModelForm):
    num_spaces_per_layer = forms.IntegerField(required=False, label="Number of Spaces per Layer", initial=60)
    remove_layer_number = forms.ChoiceField(required=False, label="Layer Number to Remove")
    remove_rack_name = forms.ModelChoiceField(queryset=Location.objects.values_list('rack_name', flat=True).distinct(), required=False, label="Rack Name to Remove")

    class Meta:
        model = Location
        fields = ['rack_name', 'layer_number', 'num_spaces_per_layer', 'remove_layer_number', 'remove_rack_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['layer_number'].widget.attrs.update({'min': 1})
        self.fields['layer_number'].validators.append(MinValueValidator(1))

        if 'remove_rack_name' in self.data:
            try:
                rack_name = self.data.get('remove_rack_name')
                self.fields['remove_layer_number'].choices = [
                    (layer, layer) for layer in Location.objects.filter(rack_name=rack_name).values_list('layer_number', flat=True).distinct()
                ]
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            self.fields['remove_layer_number'].choices = [
                (layer, layer) for layer in Location.objects.filter(rack_name=self.instance.rack_name).values_list('layer_number', flat=True).distinct()
            ]

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
    
    @transaction.atomic
    def save(self, commit=True):
        status_transition = super().save(commit=False)
        if commit:
            status_transition.save()
        return status_transition

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

    @transaction.atomic
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
    

class CheckinOrUpdateForm(forms.Form):
    ACTION_CHOICES = [
        ('checkin_new', 'Check-in For New'),
        ('checkin_location', 'Check-in/Update Location'),
    ]

    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    sn = forms.CharField(max_length=13, required=False, validators=[RegexValidator(regex=r'^\d{13}$', message='SN must be exactly 13 digits', code='invalid_sn')])
    short_12V_48V = forms.ChoiceField(choices=[('P', 'Pass'), ('F12', 'Fail on 12V'), ('F48', 'Fail on 48V')], required=False, initial='P')
    priority_level = forms.ChoiceField(choices=PRIORITY_LEVEL_CHOICES, required=False, initial='Normal')
    rack_name = forms.ChoiceField(choices=[], required=False, label="Rack")
    layer_number = forms.ChoiceField(choices=[], required=False, label="Layer")
    space_number = forms.ChoiceField(choices=[], required=False, label="Space")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
        self.fields['sn'].widget.attrs.update({'class': 'form-control'})
        self.fields['short_12V_48V'].widget.attrs.update({'class': 'form-control'})
        self.fields['priority_level'].widget.attrs.update({'class': 'form-control'})
        self.fields['rack_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['layer_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['space_number'].widget.attrs.update({'class': 'form-control'})


# Formsets for featureManageView
CategoryFormSet = modelformset_factory(Category, form=CategoryForm, extra=1, can_delete=False)
StatusFormSet = modelformset_factory(Status, form=StatusForm, extra=1, 
                                     labels={'name': 'Status Name', 'is_closed': 'Is Closed?'})
TaskFormSet = modelformset_factory(Task, form=TaskForm, extra=1, can_delete=False)
StatusTaskFormSet = modelformset_factory(StatusTask, form=StatusTaskForm, extra=1, can_delete=True)
LocationFormSet = modelformset_factory(Location, form=LocationForm, extra=1, can_delete=True)