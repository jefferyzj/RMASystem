from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, UpdateView, CreateView, FormView
from django.urls import reverse_lazy
from .models import Product, ProductTask, Category, Task, Location, Status, StatusTransition, ProductStatus, StatusTask
from .forms import ProductForm, ProductTaskForm, TaskForm, LocationForm, StatusTransitionForm, CheckinOrUpdateForm, CategoryForm
from django.core.exceptions import ValidationError
from django_filters.views import FilterView
from .filters import ProductFilter
from django.contrib import messages
from django.http import JsonResponse
from .forms import CategoryFormSet, StatusFormSet, TaskFormSet, LocationFormSet
from .utilhelpers import PRIORITY_LEVEL_CHOICES

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

class CheckinOrUpdateView(FormView):
    template_name = 'checkin_or_update.html'
    form_class = CheckinOrUpdateForm

    def form_valid(self, form):
        action = form.cleaned_data['action']
        if action == 'checkin_new':
            # Handle check-in for new product
            category = form.cleaned_data['category']
            sn = form.cleaned_data['sn']
            short_12V_48V = form.cleaned_data['short_12V_48V']
            priority_level = form.cleaned_data['priority_level']
            # Check if the SN already exists
            if Product.objects.filter(SN=sn).exists():
                form.add_error('sn', 'A product with this SN already exists.')
                return self.form_invalid(form)
            # Create the new product
            product = Product.objects.create(SN=sn, category=category, short_12V_48V=short_12V_48V, priority_level=priority_level)
            messages.success(self.request, f'Product successfully created: Category: {product.category.name}, SN: {product.SN}, Short 12V/48V: {product.short_12V_48V}, Priority Level: {product.get_priority_level_display()}.')
            return self.render_to_response(self.get_context_data(form=form))
        elif action == 'checkin_location':
            # Handle check-in/update location
            sn = form.cleaned_data['sn']
            rack_name = form.cleaned_data['rack_name']
            layer_number = form.cleaned_data['layer_number']
            space_number = form.cleaned_data['space_number']
            # Check if the SN exists
            try:
                product = Product.objects.get(SN=sn)
            except Product.DoesNotExist:
                form.add_error('sn', 'Check-in location action failed. Please check-in the product first.')
                return self.form_invalid(form)
            # Ensure the new location is an existing but empty location
            try:
                location = Location.objects.get(rack_name=rack_name, layer_number=layer_number, space_number=space_number, product__isnull=True)
            except Location.DoesNotExist:
                form.add_error('rack_name', 'The selected location is not available.')
                return self.form_invalid(form)
            product.location = location
            product.save()
            messages.success(self.request, f'Product location updated: SN: {product.SN}, Rack: {location.rack_name}, Layer: {location.layer_number}, Space: {location.space_number or "N/A"}.')
            return self.render_to_response(self.get_context_data(form=form))
        # Handle other actions later
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['racks'] = Location.objects.values_list('rack_name', flat=True).distinct()
        return context

    def get_layers(self, rack_name):
        layers = Location.objects.filter(rack_name=rack_name, product__isnull=True).values_list('layer_number', flat=True).distinct()
        return layers

    def get_spaces(self, rack_name, layer_number):
        spaces = Location.objects.filter(rack_name=rack_name, layer_number=layer_number, product__isnull=True).values_list('space_number', flat=True).distinct()
        return spaces

    def get_product_location(self, request):
        sn = request.GET.get('sn')
        try:
            product = Product.objects.get(SN=sn)
            location = product.location
            current_status = product.current_status
            data = {
                'location': {
                    'rack_name': location.rack_name if location else None,
                    'layer_number': location.layer_number if location else None,
                    'space_number': location.space_number if location else None,
                },
                'current_status': current_status.name if current_status else 'No status'
            }
        except Product.DoesNotExist:
            data = {'error': 'Product not found'}
        return JsonResponse(data)

class FeatureManageView(View):
    template_name = 'feature_manage.html'

    def get(self, request):
        action = request.GET.get('form_action', 'category')
        formsets = {
            'category': CategoryFormSet(queryset=Category.objects.all()),
            'status': StatusFormSet(queryset=Status.objects.all()),
            'task': TaskFormSet(queryset=Task.objects.all()),
            'location': LocationFormSet(queryset=Location.objects.all()),  # Ensure the queryset is not empty
        }
        category_form = CategoryForm()
        task_form = TaskForm()
        categories_exist = Category.objects.exists()
        return render(request, self.template_name, {
            'formsets': formsets,
            'selected_action': action,
            'category_form': category_form,
            'task_form': task_form,
            'categories_exist': categories_exist,
        })

    def post(self, request):
        action = request.POST.get('form_action', 'category')
        print(f"Action: {action}")  # Debug statement to print the action value
        formsets = {
            'category': CategoryFormSet(request.POST),
            'status': StatusFormSet(request.POST),
            'task': TaskFormSet(request.POST),
            'location': LocationFormSet(request.POST),
        }
        category_form = CategoryForm(request.POST)
        task_form = TaskForm(request.POST)

        if action == 'category':
            category_action = request.POST.get('category_action')
            if category_action == 'add':
                if category_form.is_valid():
                    category_form.save()
                    messages.success(request, 'Category added successfully.')
                    return redirect('feature_manage')
                else:
                    print(category_form.errors)  # Debug statement to print form errors
            elif category_action == 'delete':
                category = get_object_or_404(Category, pk=request.POST.get('category'))
                product_count = Product.objects.filter(category=category).count()
                if product_count > 0:
                    messages.error(request, f'Cannot delete category "{category.name}" because it has {product_count} products.')
                else:
                    category.delete()
                    messages.success(request, 'Category deleted successfully.')
                return redirect('feature_manage')

        if action == 'task':
            task_action = request.POST.get('task_action')
            if task_action == 'add':
                if task_form.is_valid():
                    task_form.save()
                    messages.success(request, 'Task added successfully.')
                    return redirect('feature_manage')
                else:
                    print(task_form.errors)  # Debug statement to print form errors
            elif task_action == 'delete':
                task_id = request.POST.get('existingTasksSet')
                if task_id:
                    task = get_object_or_404(Task, pk=task_id)
                    task.delete()
                    messages.success(request, 'Task deleted successfully.')
                    return redirect('feature_manage')

        if action in formsets and formsets[action].is_valid():
            formsets[action].save()
            messages.success(request, f'{action.capitalize()}s updated successfully.')
            return redirect('feature_manage')
        else:
            if action not in formsets:
                print(f"Invalid action: {action}")  # Debug statement to print invalid action
            else:
                print(formsets[action].errors)  # Debug statement to print formset errors

        return render(request, self.template_name, {
            'formsets': formsets,
            'selected_action': action,
            'category_form': category_form,
            'task_form': task_form,
            'categories_exist': Category.objects.exists(),
        })
    
def get_predefined_tasks(request):
    status_id = request.GET.get('status_id')
    if status_id:
        tasks = StatusTask.objects.filter(status_id=status_id, is_predefined=True).values('task__task_name', 'order')
        tasks_list = list(tasks)
        return JsonResponse({'tasks': tasks_list})
    return JsonResponse({'tasks': []})