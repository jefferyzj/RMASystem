from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from model_utils.models import TimeStampedModel, SoftDeletableModel
import uuid
from .utilhelpers import PRIORITY_LEVEL_CHOICES
from ordered_model.models import OrderedModel
from django.db.models import Q
from django.core.exceptions import ValidationError




class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Location(models.Model):
    rack_name = models.CharField(max_length=100, default='None Rack')
    layer_number = models.IntegerField(default=-1)
    space_number = models.IntegerField(default=-1)

    class Meta:
        unique_together = ('rack_name', 'layer_number', 'space_number')

    def __str__(self):
        return f'{self.rack_name} - Layer {self.layer_number} - Space {self.space_number}'

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

class StatusTransition(TimeStampedModel):
    from_status = models.ForeignKey(Status, related_name='transitions_from', on_delete=models.CASCADE)
    to_status = models.ForeignKey(Status, related_name='transitions_to', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.from_status} -> {self.to_status}'
    
    def save(self, *args, **kwargs):
        if self.from_status.is_closed:
            raise ValidationError(f"Cannot create a transition from a closed status: {self.from_status.name}")
        super().save(*args, **kwargs)

class Task(TimeStampedModel):
    action = models.CharField(
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
        return f"This Task: Action: {self.action} | description: {self.description}."

class StatusTask(OrderedModel):
    status = models.ForeignKey(Status, related_name='status_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='task_statuses', on_delete=models.CASCADE)
    is_predefined = models.BooleanField(default=True, help_text="Indicates if the task is predefined for this status")
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    
    order_with_respect_to = 'status'

    class Meta(OrderedModel.Meta):
        ordering = ['order']

    def __str__(self):
        return f'- The task {self.task.action} under - status {self.status.name} - with the order {self.order}' 
    
class ProductTask(TimeStampedModel):
    product = models.ForeignKey('Product', related_name='tasks_of_product', on_delete=models.CASCADE)
    task = models.ForeignKey('Task', related_name='products_of_task', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    is_predefined = models.BooleanField(default=False, help_text="Indicates if the task was added automatically")
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'task'],
                condition=models.Q(is_completed=False, is_skipped=False),
                name='unique_active_product_task'
            )
        ]

    def __str__(self):
        return f'{self.product.SN} - {self.task.action} - is completed: {self.is_completed} - is skipped: {self.is_skipped} - result: {self.result}'
    
    def update_task(self, is_now_completed=False, is_now_skipped=False, result=None, note=None):
        if not self.is_completed and not self.is_skipped:
            self.is_completed = is_now_completed
            self.is_skipped = is_now_skipped
            if result is not None:
                self.result = result
        if note is not None:
            self.note = note
        self.save()

        #if update the current task as completed or skipped, then we need to locate the current task of the product
        if is_now_completed or is_now_skipped:
            self.product.locate_current_task()

        

    def skip_task(self):
        if self.is_completed or self.is_skipped:
            raise ValueError("Cannot skip a task that has already been completed or skipped.")
        
        #set the task as skipped
        self.is_skipped = True
        #append the 'Skipped' to the front of the result
        self.result = f'Skipped - {self.result}'
        self.save()

        if self.product.current_task == self.task:
            self.product.current_task = self.product.locate_current_task()
            self.product.save(update_fields=['current_task'])
        
class ProductStatus(TimeStampedModel):
    product = models.ForeignKey('Product', related_name='status_history_of_product', on_delete=models.CASCADE)
    status = models.ForeignKey(Status, related_name='products_under_status', on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.SN} - {self.status.name} at {self.changed_at}'
    
    #TODO: need to adjust this method because the result of task had moved to the ProductTask model
    #Done: adjust the method to get the result of the task from the ProductTask model
    def get_product_status_result(self):
        product_tasks = ProductTask.objects.filter(
            product=self.product, 
            task__statustask__status=self.status
            ).select_related('task'
            ).order_by('task__statustask__created')

        result = f'{self.status.name}: '
        for product_task in product_tasks:
            task_situation = 'Completed' if product_task.is_completed else 'Skipped' if product_task.is_skipped else 'Not Yet Done'
            result += f'{product_task.task.action} - is {task_situation} - Result: {product_task.result}'
            if  product_tasks.note:
                result += f' - Note: {product_task.note}'
            result += ' | '
        return result

class Product(TimeStampedModel, SoftDeletableModel):
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
    
    #here the current_status map to the Status model, and the current_task map to the Task model
    #Take care of the case that we actually need productStatus and productTask instances instead
    current_status = models.ForeignKey('Status', related_name='ALL_products', on_delete=models.CASCADE, null=True, blank=True)
    current_task = models.ForeignKey('Task', related_name='All_products', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.OneToOneField('Location', on_delete=models.CASCADE, related_name='product', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['SN'], name='unique_sn_constraint'),
            models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits_constraint'),
            models.UniqueConstraint(fields=['location'], name='unique_product_location_constraint')
        ]

    def __str__(self):
        current_task_action = self.current_task.action if self.current_task else "No task assigned"
        return f'Product SN: {self.SN} | Priority: {self.priority_level} | Current Status: {self.current_status.name if self.current_status else "No status"} | Action of Task: {current_task_action.action}'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        previous_status = None

        if is_new:
            self._initialize_new_product()
        else:
            previous_status = self._update_existing_product_status()

        super().save(*args, **kwargs)

        if not is_new and previous_status != self.current_status:
            self._handle_if_status_change()

    def _initialize_new_product(self):
        rma_sorting_status, created = Status.objects.get_or_create(name="RMA Sorting")
        self.change_status(rma_sorting_status)
        self._locate_current_task()


    def _update_existing_product_status(self):
        previous_status = Product.objects.get(pk=self.pk).current_status
        super().save(update_fields=['current_status'])
        return previous_status

    def _handle_if_status_change(self):
        ProductStatus.objects.create(product=self, status=self.current_status)
        self._locate_current_task()
        if self.current_status.is_closed:
            self.location = None
            self.current_task = None
            super().save(update_fields=['location'])
        #current_task had been saved in the locate_current_task method
        #current_status had been saved in the _change_status_ method    
                        
 
    
    """"change the status of the product to the new status abd assign the predefined tasks of the new status to the product"""
    def change_status(self, new_status):

        # Check if all tasks under the current status are completed or skipped
        incomplete_tasks = self.tasks_of_product.filter(
            is_completed=False, 
            is_skipped=False, 
            task__statustask__status=self.current_status
        )
        if incomplete_tasks.exists():
            raise ValidationError("All tasks under the current status must be completed or skipped before changing the status.")
        
        self.current_status = new_status
        self.assign_predefined_tasks_by_status()  


    #every time before we call this method, we need to make sure that the current_task is not None or the producttask of current_task is inactivated already.
    #return the current task of the product after locating
    """locate the current task of the product and save it to the current_task field"""
    def _locate_current_task(self):
        
        first_active_producttask = self.tasks_of_product.filter(is_completed=False, is_skipped = False).select_related('task__statustask').order_by('task__statustask__order').first()
        current_producttask = self.tasks_of_product.filter(task=self.current_task).first()
        new_current_productTask = first_active_producttask if first_active_producttask else None

        if current_producttask != new_current_productTask:
            self.current_task = new_current_productTask.task if new_current_productTask else None
            self.save(update_fields=['current_task'])

        return self.current_task

    def assign_predefined_tasks_by_status(self):
        status_tasks_predefined = self.current_status.status_tasks.filter(is_predefined=True).order_by('order')
        for status_task in status_tasks_predefined:
            ProductTask.objects.create(product=self, task=status_task.task, is_predefined=True)

    def assign_tasks(self, task, set_as_predefined_of_status=False):
        # Check if a StatusTask with the same status and task already exists
        if not StatusTask.objects.filter(status=self.current_status, task=task).exists():
            StatusTask.objects.create(
                status=self.current_status,
                task=task,
                defaults={'is_predefined': set_as_predefined_of_status}
            )
        # Create a ProductTask for the product
        ProductTask.objects.create(product=self, task=task, is_predefined=set_as_predefined_of_status)

    def insert_task_at_position(self, task, position, set_as_predefined_of_status=False):
        # Get the number of completed tasks
        num_inactive_tasks = self.tasks_of_product.filter(Q(is_completed=True) | Q(is_skipped = True)).count()

        # Check if the target position is within the range of completed tasks
        if position <= num_inactive_tasks:
            raise ValueError("Cannot insert a task at a position within the range of completed or skipped tasks.")

        # Create the new task at the specified position
        status_task = StatusTask.objects.create(
            status=self.current_status,
            task=task,
            is_predefined=set_as_predefined_of_status
        )
        
        # Move the task to the specified position
        status_task.to(position - 1)  # `to` method uses zero-based index
        
        # Assign the task to the product
        ProductTask.objects.create(product=self, task=task, is_predefined=set_as_predefined_of_status)

    def get_all_tasks(self, only_active=False):
        tasks = self.tasks_of_product.select_related('task__statustask__status').order_by(
            'task__statustask__status__created', 'task__statustask__order'
        )
        if only_active:
            tasks = tasks.filter(is_completed=False, is_skipped=False)
        return tasks


    def get_ongoing_task(self):
        return self.task_of_product.filter(Q(task = self.current_task) and Q(is_completed = False) and Q(is_skipped = False))



    def get_possible_next_statuses(self):
        return self.current_status.get_possible_next_statuses()

    def list_status_result_history(self):
        all_product_statuses = self.status_history_of_product.order_by('changed_at')
        history = [f'Product SN: {self.SN}']
        for product_status in all_product_statuses:
            status_result = product_status.get_product_status_result()
            history.append(f'{status_result} at {product_status.changed_at}')
        return "\n".join(history)
    

    #TODO: (Checked)need to improve the way to retrieve the instances with related name, 
    #TODO: Make some change to product save(), but still need to test and verify the change. 
    
    