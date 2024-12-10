from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, UpdateView, CreateView, FormView
from django.urls import reverse_lazy
from .models import Product, ProductTask, Category, Task, Location, Status, StatusTransition, ProductStatus, StatusTask
from .forms import ProductForm, ProductTaskForm, TaskForm, LocationForm, StatusTransitionForm, CategoryForm, StatusTaskForm, StatusForm
from django.core.exceptions import ValidationError
from django_filters.views import FilterView
from .filters import ProductFilter
from django.contrib import messages
from django.http import JsonResponse
from .forms import CategoryFormSet, StatusFormSet, TaskFormSet, LocationFormSet, StatusTaskFormSet
from .utilhelpers import PRIORITY_LEVEL_CHOICES
from django.db import models
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Location
from .forms import CheckinNewForm, UpdateLocationForm

def home_view(request):
    return render(request, 'base.html')

class ProductListView(FilterView):
    model = Product
    template_name = 'products.html'
    context_object_name = 'products'
    paginate_by = 10
    filterset_class = ProductFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category__name__in=categories)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['locations'] = Location.objects.all()
        context['priority_levels'] = PRIORITY_LEVEL_CHOICES
        context['statuses'] = Status.objects.all()
        context['tasks'] = Task.objects.all()
        return context

class ProductDetailView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_detail.html'
    slug_field = 'SN'
    slug_url_kwarg = 'sn'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['status_history'] = product.list_status_result_history()
        return context

    def form_valid(self, form):
        new_location_name = form.cleaned_data.get('new_location')
        if new_location_name:
            new_location, created = Location.objects.get_or_create(rack_name=new_location_name)
            form.instance.location = new_location
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('product_detail', kwargs={'sn': self.object.SN})

class ProductStatusTaskEditView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_status_task_edit.html'
    slug_field = 'SN'
    slug_url_kwarg = 'sn'
    context_object_name = 'product'

    def get_success_url(self):
        return reverse_lazy('product_detail', kwargs={'sn': self.object.SN})

class ProductTaskView(View):
    def get(self, request, sn):
        product = get_object_or_404(Product, SN=sn)
        ongoing_task = ProductTask.objects.filter(product=product, is_completed=False).first()
        form = ProductTaskForm(instance=ongoing_task)
        return render(request, 'product_task.html', {'form': form, 'product': product, 'ongoing_task': ongoing_task})

    def post(self, request, task_id):
        task = get_object_or_404(ProductTask, id=task_id)
        form = ProductTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('product_task', sn=task.product.SN)
        return render(request, 'product_task.html', {'form': form, 'product': task.product, 'ongoing_task': task})

class AddTaskView(CreateView):
    form_class = TaskForm
    template_name = 'add_task.html'

    def form_valid(self, form):
        product = get_object_or_404(Product, SN=self.kwargs['sn'])
        form.instance.product = product
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('product_edit', kwargs={'sn': self.kwargs['sn']})

class LocationCreateView(CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'location_form.html'

    def get_success_url(self):
        return reverse_lazy('location_list')

class LocationListView(ListView):
    model = Location
    template_name = 'locations.html'
    context_object_name = 'locations'

class StatusTransitionView(FormView):
    form_class = StatusTransitionForm
    template_name = 'transition_status.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product_id = self.kwargs['product_id']
        self.product = get_object_or_404(Product, pk=product_id)
        kwargs['product'] = self.product
        return kwargs

    def form_valid(self, form):
        new_status = form.cleaned_data['to_status']
        new_status_name = form.cleaned_data['new_status_name']
        possible_next_statuses = form.cleaned_data.get['possible_next_statuses', []]

        if new_status_name:
            new_status, created = Status.objects.get_or_create(name=new_status_name)
            if created:
                # Create a new StatusTransition to remember the mapping
                for next_status in possible_next_statuses:
                    StatusTransition.objects.create(from_status=new_status, to_status=next_status)
        # Transition to the new status
        self.product.current_status = new_status
        self.product.save()

        return redirect('product_detail', pk=self.product.pk)


class FeatureManageView(View):
    template_name = 'feature_manage.html'

    def get(self, request):
        return render(request, self.template_name)

class ManageCategoriesView(View):
    template_name = 'manage_categories.html'

    def get(self, request):
        print("ManageCategoriesView GET request")
        category_form = CategoryForm()
        categories_exist = Category.objects.exists()
        print("Rendering manage_categories.html template")
        return render(request, self.template_name, {
            'category_form': category_form,
            'categories_exist': categories_exist
        })

    def post(self, request):
        print("ManageCategoriesView POST request")
        category_form = CategoryForm(request.POST)
        category_action = request.POST.get('category_action')
        print(f"Category action: {category_action}")
        if category_action == 'add':
            if category_form.is_valid():
                category_form.save()
                messages.success(request, 'Category added successfully.')
                print("Category added successfully")
            else:
                messages.error(request, 'Error adding category.')
                print("Error adding category")
        elif category_action == 'delete':
            category = get_object_or_404(Category, pk=request.POST.get('category'))
            product_count = Product.objects.filter(category=category).count()
            if product_count > 0:
                messages.error(request, f'Cannot delete category "{category.name}" because it has {product_count} products.')
                print(f"Cannot delete category {category.name} because it has {product_count} products")
            else:
                category.delete()
                messages.success(request, 'Category deleted successfully.')
                print("Category deleted successfully")
        categories_exist = Category.objects.exists()
        return render(request, self.template_name, {
            'category_form': category_form,
            'categories_exist': categories_exist
        })

class ManageStatusesView(View):
    template_name = 'manage_statuses.html'

    def get(self, request):
        print("ManageStatusesView GET request")
        formset = StatusFormSet(queryset=Status.objects.none())  # Only include empty forms for adding
        transitions = StatusTransition.get_all_transitions_by_status()
        statuses = Status.objects.all()
        print("Rendering manage_statuses.html template")
        return render(request, self.template_name, {
            'formset': formset,
            'statuses': statuses,
            'transitions': transitions
        })
    
    def post(self, request):
        print("ManageStatusesView POST request")
        status_action = request.POST.get('status_action')
        print(f"Got Status action: {status_action}")
        if status_action == 'add':
            formset = StatusFormSet(request.POST)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Statuses updated successfully.')
                print("Statuses updated successfully")
            else:
                messages.error(request, 'Error updating statuses.')
                print("Error updating statuses")
        elif status_action == 'delete':
            status_id = request.POST.get('status_id')
            status = get_object_or_404(Status, pk=status_id)
            if ProductStatus.objects.filter(status=status).exists():
                messages.error(request, 'Cannot delete status with associated products.')
                print("Cannot delete status with associated products")
            elif StatusTask.objects.filter(status=status).exists():
                messages.error(request, 'Cannot delete status with associated tasks.')
                print("Cannot delete status with associated tasks")
            else:
                StatusTransition.objects.filter(from_status=status).delete()
                StatusTransition.objects.filter(to_status=status).delete()
                print(f"StatusTransition related to {status} deleted successfully")
                status.delete()
                messages.success(request, 'Status deleted successfully.')
                print("Status deleted successfully")
        
        formset = StatusFormSet(queryset=Status.objects.none())  # Only include empty forms for adding
        transitions = StatusTransition.get_all_transitions_by_status()
        statuses = Status.objects.all()
        return render(request, self.template_name, {
            'formset': formset,
            'statuses': statuses,
            'transitions': transitions
        })

class ManageTasksView(View):
    template_name = 'manage_tasks.html'

    def get(self, request):
        print("ManageTasksView GET request")
        task_form = TaskForm()
        status_task_form = StatusTaskForm()
        existing_tasks = StatusTask.get_existing_tasks_choices(show_desc=True)
        print("Rendering manage_tasks.html template")
        return render(request, self.template_name, {
            'task_form': task_form,
            'status_task_form': status_task_form,
            'existing_tasks': existing_tasks
        })
    
    def post(self, request):
        print("ManageTasksView POST request")
        task_form = TaskForm(request.POST)
        status_task_form = StatusTaskForm(request.POST)
        task_action = request.POST.get('task_action')
        print(f"Task action: {task_action}")
        if task_action == 'add':
            if task_form.is_valid():
                task = task_form.save(commit=False)
                existing_status = request.POST.get('status')
                is_predefined = request.POST.get('is_predefined')
                order = request.POST.get('order')
                # Add task to database with task_form.save since they do the same thing as task.save.
                # If counter error, task will be deleted
                task_form.save() 
                if existing_status:                 
                    status_task_form = StatusTaskForm({
                        'status': existing_status,
                        'task': task.pk,
                        'is_predefined': is_predefined,
                        'order': order
                    })
                    if status_task_form.is_valid():
                        status_task_form.save()
                        if is_predefined and order:
                            messages.success(request, 'Predefined Task mapped to status with order created successfully.')
                            print("Statustask added with predefined and order successfully")
                        else:
                            messages.success(request, 'Non-predefined Task mapped to status without order created successfully.')
                            print("Statustask added without predefined and order successfully")
                    else:
                        messages.error(request, 'Error adding StatusTask.')
                        print(status_task_form.errors)
                        task.delete()
                        print("Error adding StatusTask because status_task_form is invalid")
                else:
                    messages.success(request, 'Task added successfully.')
                    print("Task added successfully without mapping to status")
            else:
                messages.error(request, 'Error adding task.')
                task.delete()
                print("Error adding task because task_form is invalid")
        
        elif task_action == 'delete':
            selected_task_pk = request.POST.get('existing_tasks')
            print(f"Selected task PK: {selected_task_pk}")
            if selected_task_pk:
                try:
                    # Try to retrieve as StatusTask first
                    status_task = StatusTask.objects.get(pk=selected_task_pk)
                    task = status_task.task
                    product_count = ProductTask.objects.filter(task=task).count()
                    if product_count > 0:
                        messages.error(request, 'Cannot delete task with associated products.')
                        print("Cannot delete task with associated products")
                    else:
                        status_task.delete()
                        task.delete()
                        messages.success(request, 'StatusTask and associated Task deleted successfully.')
                        print("StatusTask and associated Task deleted successfully")
                except StatusTask.DoesNotExist:
                    # If not a StatusTask, try to retrieve as Task
                    try:
                        task = Task.objects.get(pk=selected_task_pk)
                        product_count = ProductTask.objects.filter(task=task).count()
                        if product_count > 0:
                            messages.error(request, 'Cannot delete task with associated products.')
                            print("Cannot delete task with associated products")
                        else:
                            task.delete()
                            messages.success(request, 'Task deleted successfully.')
                            print("Task deleted successfully")
                    except Task.DoesNotExist:
                        messages.error(request, 'Task not found.')
                        print("Task not found")

        
        task_form = TaskForm()
        status_task_form = StatusTaskForm()
        existing_tasks = StatusTask.get_existing_tasks_choices(show_desc=True)
        return render(request, self.template_name, {
            'task_form': task_form,
            'status_task_form': status_task_form,
            'existing_tasks': existing_tasks
        })


class ManageLocationsView(View):
    template_name = 'manage_locations.html'

    def get(self, request):
        form = LocationForm()
        racks = Location.objects.values('rack_name').annotate(
            layers=models.Count('layer_number', distinct=True)
        ).order_by('rack_name')
        rack_layers = []
        for rack in racks:
            layers = Location.objects.filter(rack_name=rack['rack_name']).values('layer_number').annotate(
                product_count=models.Count('product', filter=models.Q(product__isnull=False))
            ).order_by('layer_number')
            rack_layers.append({
                'rack_name': rack['rack_name'],
                'layers': layers
            })
        return render(request, self.template_name, {
            'form': form,
            'racks': rack_layers
        })

    def post(self, request):
        form = LocationForm(request.POST)
        location_action = request.POST.get('location_action')
        if location_action == 'add':
            if form.is_valid():
                rack_name = form.cleaned_data.get('rack_name')
                layer_number = form.cleaned_data.get('layer_number')
                num_spaces_per_layer = form.cleaned_data.get('num_spaces_per_layer') or 60

                if not rack_name or not layer_number:
                    messages.error(request, "You must specify both a rack name and a layer number when creating locations.")
                elif Location.objects.filter(rack_name=rack_name, layer_number=layer_number).exists():
                    messages.error(request, "Locations with the specified rack name and layer already exist.")
                else:
                    for space in range(1, num_spaces_per_layer + 1):
                        Location.objects.create(
                            rack_name=rack_name,
                            layer_number=layer_number,
                            space_number=space
                        )
                    messages.success(request, 'Location(s) created successfully.')
            else:
                messages.error(request, 'Error creating location(s).')
        elif location_action == 'delete':
            rack_name = request.POST.get('remove_rack_name')
            layer_number = request.POST.get('remove_layer_number')

            if not rack_name or not layer_number:
                messages.error(request, "You must specify both a rack name and a layer number when removing locations.")
            elif Location.objects.filter(rack_name=rack_name, layer_number=layer_number, product__isnull=False).exists():
                messages.error(request, "Cannot remove locations in this layer because some locations store products.")
            else:
                Location.objects.filter(rack_name=rack_name, layer_number=layer_number, product__isnull=True).delete()
                messages.success(request, 'Location(s) removed successfully.')

        racks = Location.objects.values('rack_name').annotate(
            layers=models.Count('layer_number', distinct=True)
        ).order_by('rack_name')
        rack_layers = []
        for rack in racks:
            layers = Location.objects.filter(rack_name=rack['rack_name']).values('layer_number').annotate(
                product_count=models.Count('product', filter=models.Q(product__isnull=False))
            ).order_by('layer_number')
            rack_layers.append({
                'rack_name': rack['rack_name'],
                'layers': layers
            })
        return render(request, self.template_name, {
            'form': form,
            'racks': rack_layers
        })

class CheckinView(View):
    template_name = 'checkin.html'

    def get(self, request):
        return render(request, self.template_name)


class CheckinNewView(View):
    template_name = 'checkin_new.html'

    def get(self, request):
        form = CheckinNewForm()
        racks = Location.objects.values('rack_name').distinct()
        return render(request, self.template_name, {'form': form, 'racks': racks})

    def post(self, request):
        form = CheckinNewForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data.get('category')
            sn = form.cleaned_data.get('sn')
            short_12V_48V = form.cleaned_data.get('short_12V_48V')
            priority_level = form.cleaned_data.get('priority_level')
            rack_name = form.cleaned_data.get('rack_name')
            layer_number = form.cleaned_data.get('layer_number')
            space_number = form.cleaned_data.get('space_number')

            product, created = Product.objects.get_or_create(sn=sn, defaults={
                'category': category,
                'short_12V_48V': short_12V_48V,
                'priority_level': priority_level,
                'location': Location.objects.get(rack_name=rack_name, layer_number=layer_number, space_number=space_number)
            })

            if not created:
                product.location = Location.objects.get(rack_name=rack_name, layer_number=layer_number, space_number=space_number)
                product.save()

            messages.success(request, 'Product checked in successfully.')
            return redirect('checkin_new')
        else:
            messages.error(request, 'Error checking in product.')
        racks = Location.objects.values('rack_name').distinct()
        return render(request, self.template_name, {'form': form, 'racks': racks})

class UpdateLocationView(View):
    template_name = 'update_location.html'

    def get(self, request):
        form = UpdateLocationForm()
        racks = Location.objects.values('rack_name').distinct()
        return render(request, self.template_name, {'form': form, 'racks': racks})

    def post(self, request):
        form = UpdateLocationForm(request.POST)
        if form.is_valid():
            sn = form.cleaned_data.get('sn')
            rack_name = form.cleaned_data.get('rack_name')
            layer_number = form.cleaned_data.get('layer_number')
            space_number = form.cleaned_data.get('space_number')

            try:
                product = Product.objects.get(sn=sn)
                product.location = Location.objects.get(rack_name=rack_name, layer_number=layer_number, space_number=space_number)
                product.save()
                messages.success(request, 'Product location updated successfully.')
            except Product.DoesNotExist:
                messages.error(request, 'Product with the specified serial number does not exist.')

            return redirect('update_location')
        else:
            messages.error(request, 'Error updating product location.')
        racks = Location.objects.values('rack_name').distinct()
        return render(request, self.template_name, {'form': form, 'racks': racks})

@require_GET   
def get_predefined_tasks(request):
    """
    helper function to fetch predefined tasks that use in manage_tasks.html
    """
    status_id = request.GET.get('status_id')
    if status_id:
        tasks = StatusTask.objects.filter(status_id=status_id, is_predefined=True).values('task__task_name', 'order')
        tasks_list = list(tasks)
        return JsonResponse({'tasks': tasks_list})
    return JsonResponse({'tasks': []})

@require_GET
def get_order_choices(request):
    """
    helper function to fetch order choices that use in manage_tasks.html
    """
    status_id = request.GET.get('status_id')
    if status_id:
        predefined_tasks = StatusTask.objects.filter(status_id=status_id, is_predefined=True).order_by('order')
        max_order = predefined_tasks.count() + 1
        choices = [{'value': i, 'display': i} for i in range(1, max_order + 1)]
        return JsonResponse({'choices': choices})
    return JsonResponse({'choices': []})

@require_GET
def fetch_categories(request):
    """
    helper function to fetch categories that use in manage_categories.html
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        categories = Category.objects.annotate(product_count=Count('products'))
        data = [{'name': category.name, 'product_count': category.product_count} for category in categories]
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@require_GET
def get_layers_for_rack(request):
    rack_name = request.GET.get('rack_name')
    if rack_name:
        layers = Location.objects.filter(rack_name=rack_name).values('layer_number').annotate(
            product_count=models.Count('product', filter=models.Q(product__isnull=False))
        ).distinct()
        return JsonResponse({'layers': list(layers)})
    return JsonResponse({'layers': []})
@require_GET
def get_spaces_for_layer(request):
    rack_name = request.GET.get('rack_name')
    layer_number = request.GET.get('layer_number')
    if rack_name and layer_number:
        spaces = Location.objects.filter(rack_name=rack_name, layer_number=layer_number).values_list('space_number', flat=True)
        return JsonResponse({'spaces': list(spaces)})
    return JsonResponse({'spaces': []})