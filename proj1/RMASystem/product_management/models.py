from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from model_utils.models import TimeStampedModel, SoftDeletableModel
import uuid
from .utilhelpers import PRIORITY_LEVEL_CHOICES
from ordered_model.models import OrderedModel
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import transaction


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Location(models.Model):
    rack_name = models.CharField(max_length=100)
    layer_number = models.IntegerField()
    space_number = models.IntegerField(null=True, blank=True)
    product = models.OneToOneField('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='location_detail')

    class Meta:
        unique_together = ('rack_name', 'layer_number', 'space_number')

    def __str__(self):
        return f'{self.rack_name} - Layer {self.layer_number} - Space {self.space_number or "N/A"}'

    @staticmethod
    def create_rack_with_layers_and_spaces(rack_name, num_layers, num_spaces_per_layer):
        for layer in range(1, num_layers + 1):
            for space in range(1, num_spaces_per_layer + 1):
                Location.objects.create(rack_name=rack_name, layer_number=layer, space_number=space)

class Status(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_closed = models.BooleanField(default=False, help_text="Indicates if the status is a closed status")
    

    def __str__(self):
        return self.name
    

    def get_possible_next_statuses(self):
        transitions = StatusTransition.objects.filter(from_status=self).select_related('to_status').order_by('created')
        return [transition.to_status for transition in transitions]
    @classmethod
    def get_existing_statuses(cls):
        return cls.objects.all()

class StatusTransition(TimeStampedModel):
    from_status = models.ForeignKey(Status, related_name='transitions_from', on_delete=models.CASCADE)
    to_status = models.ForeignKey(Status, related_name='transitions_to', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.from_status} -> {self.to_status}'
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.from_status.is_closed:
            raise ValidationError(f"Cannot create a transition from a closed status: {self.from_status.name}")
        super().save(*args, **kwargs)

class Task(TimeStampedModel):
    task_name = models.CharField(
        max_length=100, 
        help_text="Action to be performed in this task", 
        default="Default Action"
    )
    description = models.TextField(
        help_text="Detailed description of the task", 
        blank=True, 
        null=True
    )

    def __str__(self):
        return f"This Task: Action: {self.task_name} | description: {self.description}."


class StatusTask(OrderedModel):
    """
    This model is used to record the tasks linked to a status. 
    Can use predefined tasks with order to indicate if the tasks should be added to product 
    when the product is updated to the status.
    Order is just for predefined tasks.
    """
    status = models.ForeignKey(Status, related_name='status_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='task_statuses', on_delete=models.CASCADE)
    is_predefined = models.BooleanField(default=False, help_text="Indicates if the task is predefined for this status")
    order = models.PositiveIntegerField(default=1, editable=True, db_index=True)
    
    order_with_respect_to = 'status'

    class Meta(OrderedModel.Meta):
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['status', 'task'], name='unique_status_task')
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Seems that can handle the add task case and update task case.
        print(f"Before all save: {self.order}")
        order_stored  = self.order
        super().save(*args, **kwargs)
        print(f"stored order: {order_stored}")
        print(f"after fully save: {self.order}")

        if not self.is_predefined:
            # Assign to the tail of all tasks
            # since we saved before, the count here already includes the current task
            self.order = StatusTask.objects.filter(status=self.status).count()
            print(f"self.order in not predefined: {self.order}")
        else:
            self.to(order_stored)
        print(f"Before save: {self.order}")

        super().save(update_fields=['order'])

        print(f"After save: {self.order}")
        self.refresh_from_db()  # Refresh the instance to get the correct order value set by OrderedModel
        print(f"Final order: {self.order}")
        
    def __str__(self):
        return f'- The task {self.task.task_name} under - status {self.status.name} - with the order {self.order}'

class ProductTask(TimeStampedModel, OrderedModel):
    """
    This model is used to record the tasks of a product with order.
    Mark the result and note about the task and if is an active task or not for the product.
    """
    product = models.ForeignKey('Product', related_name='tasks_of_product', on_delete=models.CASCADE)
    task = models.ForeignKey('Task', related_name='products_of_task', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False, help_text="Indicates if the task is completed")
    is_skipped = models.BooleanField(default=False, help_text="Indicates if the task is skipped")
    is_predefined = models.BooleanField(default=False, help_text="Indicates if the task was added automatically")
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    result = models.TextField(
        default="Action Not Yet Done", 
        help_text="Result of the task of the product", 
        blank=True, 
        null=True
    )
    note = models.TextField(
        help_text="User can write down some notes on this task of this product", 
        blank=True, 
        null=True
    )

    order_with_respect_to = 'product'

    class Meta(OrderedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'task'],
                condition=models.Q(is_completed=False, is_skipped=False),
                name='unique_active_product_task'
            )
        ]
        ordering = ['order']

    def __str__(self):
        return f'{self.product.SN} - {self.task.task_name} - is completed: {self.is_completed} - is skipped: {self.is_skipped} - result: {self.result}'

    
    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Override the save() so that Skip or complete the task of the product, and update the result of the task.
        locate the current task for the product after the task is skipped or completed.
        """
        #let the first task of the product have the order 1
        if self._state.adding:
            max_order = self.__class__.objects.filter(product=self.product).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1

        if self.is_completed and self.is_skipped:
            raise ValueError("Cannot complete and skip a task at the same time.")
        
        if not self.is_completed and not self.is_skipped:
            if 'is_now_completed' in kwargs:
                self.is_completed = kwargs.pop('is_now_completed')
            if 'is_now_skipped' in kwargs:
                self.is_skipped = kwargs.pop('is_now_skipped')
            if 'result' in kwargs:
                self.result = kwargs.pop('result')
            if 'note' in kwargs:
                self.note = kwargs.pop('note')
        
        if self.is_skipped:
            self.result = f'(Skipped) -action: {self.task.task_name} -result:{self.result}'
        elif self.is_completed:
            self.result = f'(Completed) -action: {self.task.task_name} -result:{self.result}'

        super().save(*args, **kwargs)

        if self.is_completed or self.is_skipped:
            self.product.locate_current_task()
    
    @classmethod
    def insert_task_at_position(cls, product_task, position):
        """
        Insert the provided ProductTask at a specific position.
        """
        if product_task.is_completed or product_task.is_skipped:
            raise ValueError("Cannot change the order of a completed or skipped task.")

        # Use the built-in `to` method to move the task to the specified position
        product_task.to(position)

class ProductStatus(TimeStampedModel):
    """
    The model to link product and its status, and record the time of the status change.
    """
    product = models.ForeignKey('Product', related_name='status_history_of_product', on_delete=models.CASCADE)
    status = models.ForeignKey(Status, related_name='products_under_status', on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.SN} - {self.status.name} at {self.changed_at}'
    
    """
    Get the result of tasks of the product under the status, and return the result as a string. 
    """
    def get_product_status_result(self):
        product_tasks = ProductTask.objects.filter(
            product=self.product, 
            task__statustask__status=self.status
            ).select_related('task'
            ).order_by('task__statustask__created')

        result = f'{self.status.name}: '
        for product_task in product_tasks:
            task_situation = 'Completed' if product_task.is_completed else 'Skipped' if product_task.is_skipped else 'Not Yet Done'
            result += f'{product_task.task.task_name} - is {task_situation} - Result: {product_task.result}'
            if  product_tasks.note:
                result += f' - Note: {product_task.note}'
            result += ' | '
        return result

class Product(TimeStampedModel, SoftDeletableModel):
    """
    product model
    """
    SN = models.CharField(
        primary_key=True,
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{13}$',
                message='SN must be exactly 13 digits',
                code='invalid_sn'
            )
        ],
        help_text="Serial number must be exactly 13 digits"
    )
    category = models.ForeignKey('Category', related_name='products', on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVEL_CHOICES, default='normal', help_text="Indicates if the unit is Normal, Hot, or ZFA")
    description = models.TextField(blank=True, help_text="Notes or description of the product")
    location = models.ForeignKey('Location', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    short_12V_48V = models.CharField(
        max_length=10,
        choices=[('P', 'Pass'), ('F12', 'Fail on 12V'), ('F48', 'Fail on 48V')],
        default='P',
        help_text="Indicates if the product has a 12V or 48V short"
    )
    #current_status -> status instance, current_task -> task instance
    #Take care of the case that we actually need productStatus and productTask instances instead
    current_status = models.ForeignKey('Status', related_name='ALL_products', on_delete=models.CASCADE, null=True, blank=True)
    current_task = models.ForeignKey('Task', related_name='All_products', on_delete=models.SET_NULL, null=True, blank=True)
    

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['SN'], name='unique_sn_constraint'),
            models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits_constraint'),
            models.UniqueConstraint(fields=['location'], name='unique_product_location_constraint')
        ]

    def __str__(self):
        current_task_name = self.current_task.task_name if self.current_task else "No task assigned"
        return f'Product SN: {self.SN} | Priority: {self.priority_level} | Current Status: {self.current_status.name if self.current_status else "No status"} | Action of Task: {current_task_name}'
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Handle the case if the product is new or not, and if the status of the product is changed or not.
        If status change, assign the predefined tasks of the status to the product, and locate the current task of the product.
        """
        is_new = self.pk is None
        previous_status = None

        with transaction.atomic():
            if not is_new:
                previous_status = Product.objects.get(pk=self.pk).current_status
                if previous_status and previous_status != self.current_status:
                    if not self.is_allowed_change_status(previous_status):
                        raise ValidationError(f"All tasks under the current status-{previous_status.name}-must be completed or skipped before changing.")
                    self._handle_status_change()
            else:
                self._initialize_new_product()
            
            super().save(*args, **kwargs)

    
    def is_allowed_change_status(self, previous_status):
        active_tasks = self.tasks_of_product.filter(
            is_completed=False, 
            is_skipped=False, 
            task__statustask__status=previous_status)
        return not active_tasks.exists()


    def _initialize_new_product(self):
        rma_sorting_status, created = Status.objects.get_or_create(name="RMA Sorting")
        self.current_status = rma_sorting_status
        self.assign_predefined_tasks_by_status()
        self._locate_current_task()


    def _handle_status_change(self):
        ProductStatus.objects.get_or_create(product=self, status=self.current_status)
        self.assign_predefined_tasks_by_status()
        self._locate_current_task()
        if self.current_status.is_closed:
            if self.location:
                self.location.product = None
                self.location.save()
            self.location = None
            self.current_task = None
        #current_task had been saved in the locate_current_task method
           

    def _locate_current_task(self):
        """
        Locate the current task of the product and save it to the current_task field, and update the database.
        Can deal with current task being None or current task being completed or skipped.
        """
        # Retrieve the first active ProductTask (not completed and not skipped) ordered by the ProductTask order
        first_active_product_task = self.tasks_of_product.filter(
            is_completed=False, 
            is_skipped=False
        ).select_related('task__statustask').order_by('order').first()
        
        # Determine the new current ProductTask
        new_current_product_task = first_active_product_task if first_active_product_task else None

        # Update the current task if it has changed
        if self.current_task != (new_current_product_task.task if new_current_product_task else None):
            self.current_task = new_current_product_task.task if new_current_product_task else None
            self.save(update_fields=['current_task'])
        
        return self.current_task

    def assign_predefined_tasks_by_status(self):
        """
        Assign the predefined tasks of the current status to the product
        """
        status_tasks_predefined = self.current_status.status_tasks.filter(is_predefined=True).order_by('order')
        product_tasks = [
            ProductTask(product=self, task=status_task.task, is_predefined=True)
            for status_task in status_tasks_predefined
        ]
        ProductTask.objects.bulk_create(product_tasks)

    def assign_tasks(self, task, set_as_predefined_of_status=False):
        """
        Assign a task to the product, and update the current task of the product.
        """
        with transaction.atomic():
            # Create a StatusTask for the status and task if necessary
            StatusTask.objects.get_or_create(
                status=self.current_status,
                task=task,
                defaults={'is_predefined': set_as_predefined_of_status}
            )
            # Create a ProductTask for the product
            ProductTask.objects.get_or_create(product=self, task=task, is_predefined=set_as_predefined_of_status)
            # Locate the current task of the product
            self._locate_current_task()


    def get_all_tasks_of_product(self, only_active=False):
        """
        get all the tasks of the product, and return the queryset of the tasks ordered by the created time of the status of the task and the order of the task in the status
        The instances returned are the instances of the ProductTask model
        """
        tasks = self.tasks_of_product.select_related('task__statustask__status').order_by(
            'task__statustask__status__created', 'task__statustask__order'
        )
        if only_active:
            tasks = tasks.filter(is_completed=False, is_skipped=False)
        return tasks


    def get_ongoing_task(self):
        """
        get the ongoing task of the product as productTask instance
        """
        return self.tasks_of_product.filter(Q(task = self.current_task) 
                                            & Q(product = self) 
                                            &  Q(is_completed = False) 
                                            & Q(is_skipped = False))

    def list_status_result_history(self):
        """
        list the status result history of the product with tasks in all statuses, and return the result as a string
        """
        all_product_statuses = self.status_history_of_product.order_by('changed_at')
        history = [f'Product SN: {self.SN}']
        for product_status in all_product_statuses:
            status_result = product_status.get_product_status_result()
            history.append(f'{status_result} at {product_status.changed_at}')
        return "\n".join(history)
    






    #TODO: (Checked)need to improve the way to retrieve the instances with related name, 
    #TODO: (checked)Make some change to product save(), but still need to test and verify the change. 
    #TODO: (Checked)review the insert_task_at_position method, to see if it is needed or it is too hard to implement.
    #  ALso need to review the statusTask model, to see if it is needed for the order. 
    #TODO: (checked)go through the models.py and detected some bugs and fix them.
    #TODO: checked the views.py and forms.py especially about prodductlist, productdetail, and still need to go through the producttaskview and productstatuseditview
    #TODO: the products.html and product_detail.html need to be checked and modified. But it is almost done.
    #TODO: (checked)add checkinorupdateview and its form, and the checkinorupdate.html, also update location model to map to the product.
    #TODO: still not finish the productstatustaskeditview and its form, and the product_status_task_edit.html
    #TODO: still need to develop the page to add location, add statuses and it transition, add tasks and status task, and add category.


    #1. not finish productstatustaskeditview and its form, and the product_status_task_edit.html
    #2. modify the view of checkinorupdateview, and the checkinorupdate.html
    #3. debug the products.html and product_detail.html.
    #4. add