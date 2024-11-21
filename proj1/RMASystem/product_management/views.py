from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, DetailView, ListView, UpdateView, CreateView, FormView
from django.urls import reverse_lazy
from .models import Product, ProductTask, Category, Task, Location
from .forms import ProductForm, ProductTaskForm, TaskForm, LocationForm
from .models import Product, Status, StatusTransition
from .forms import StatusTransitionForm

class ProductListView(ListView):
    model = Product
    template_name = 'products.html'
    context_object_name = 'products'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'
    slug_field = 'SN'
    slug_url_kwarg = 'sn'

class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_edit.html'
    slug_field = 'SN'
    slug_url_kwarg = 'sn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['status_results'] = ResultOfStatus.objects.filter(product=self.object).prefetch_related('tasks').order_by('-created_at')
        return context

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

        if new_status_name:
            new_status, created = Status.objects.get_or_create(name=new_status_name)
            if created:
                # Create a new StatusTransition to remember the mapping
                StatusTransition.objects.create(from_status=self.product.current_status, to_status=new_status)

        # Transition to the new status
        self.product.current_status = new_status
        self.product.save()

        return redirect('product_detail', pk=self.product.pk)