# class Product(TimeStampedModel):
#     """
#     product model
#     """
#     SN = models.CharField(
#         primary_key=True,
#         max_length=13,
#         unique=True,
#         validators=[
#             RegexValidator(
#                 regex=r'^\d{13}$',
#                 message='SN must be exactly 13 digits',
#                 code='invalid_sn'
#             )
#         ],
#         help_text="Serial number must be exactly 13 digits"
#     )
#     category = models.ForeignKey('Category', related_name='products', on_delete=models.CASCADE)
#     priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVEL_CHOICES, default='normal', help_text="Indicates if the unit is Normal, Hot, or ZFA")
#     description = models.TextField(blank=True, help_text="Notes or description of the product")
#     location = models.ForeignKey('Location', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
#     short_12V_48V = models.CharField(
#         max_length=10,
#         choices=[('P', 'Pass'), ('F12', 'Fail on 12V'), ('F48', 'Fail on 48V')],
#         default='P',
#         help_text="Indicates if the product has a 12V or 48V short"
#     )
#     #current_status -> status instance, current_task -> task instance
#     #Take care of the case that we actually need productStatus and productTask instances instead
#     current_status = models.ForeignKey('Status', related_name='ALL_products', on_delete=models.CASCADE, null=True, blank=True)
#     current_task = models.ForeignKey('Task', related_name='All_products', on_delete=models.SET_NULL, null=True, blank=True)
    

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['SN'], name='unique_sn_constraint'),
#             models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits_constraint'),
#             models.UniqueConstraint(fields=['location'], name='unique_product_location_constraint')
#         ]

#     def __str__(self):
#         current_task_name = self.current_task.task_name if self.current_task else "No task assigned"
#         return f'Product SN: {self.SN} | Priority: {self.priority_level} | Current Status: {self.current_status.name if self.current_status else "No status"} | Action of Task: {current_task_name}'
    
    
#     @transaction.atomic
#     def save(self, *args, **kwargs):
#         """
#         Handle the case if the product is new or not, and if the status of the product is changed or not.
#         If status change, assign the predefined tasks of the status to the product, and locate the current task of the product.
#         """
#         is_new = self._state.adding
#         print(f"is new: {is_new}")
#         previous_status = None

#         with transaction.atomic():
#             if not is_new:
#                 print(f"not new, the self.pk is {self.pk}")
#                 previous_status = Product.objects.get(pk=self.pk).current_status
#                 if previous_status and previous_status != self.current_status:
#                     if not self.is_allowed_change_status(previous_status):
#                         raise ValidationError(f"All tasks under the current status-{previous_status.name}-must be completed or skipped before changing.")
#                     if previous_status.is_closed:
#                         raise ValidationError("Now in the closed status, cannot change the status.")
#                     self._handle_status_change()
#             else:
#                 self._initialize_new_product()
            
#             super().save(*args, **kwargs)

#     def is_allowed_change_status(self, previous_status):
#         active_tasks = self.tasks_of_product.filter(
#             is_removed = False,
#             is_completed=False, 
#             is_skipped=False, 
#             task__statustask__status=previous_status)
#         return not active_tasks.exists()


#     def _initialize_new_product(self):
#         rma_sorting_status, created = Status.objects.get_or_create(name="RMA Sorting")
#         self.current_status = rma_sorting_status
#         self.assign_predefined_tasks_by_status()
#         self._locate_current_task()


#     def _handle_status_change(self):
#         ProductStatus.objects.get_or_create(product=self, status=self.current_status)
#         self.assign_predefined_tasks_by_status()
#         self._locate_current_task()
#         if self.current_status.is_closed:
#             if self.location:
#                 self.location.product = None
#                 self.location.save()
#             self.location = None
#             self.current_task = None
#         #current_task had been saved in the locate_current_task method
           

#     def _locate_current_task(self):
#         """
#         Locate the current task of the product and save it to the current_task field, and update the database.
#         Can deal with current task being None or current task being completed or skipped.
#         """
#         # Retrieve the first active ProductTask (not completed and not skipped) ordered by the ProductTask order
#         first_active_product_task = self.tasks_of_product.filter(
#             is_removed = False,
#             is_completed=False, 
#             is_skipped=False
#         ).order_by('order').first()
        
#         # Determine the new current ProductTask
#         new_current_product_task = first_active_product_task if first_active_product_task else None

#         # Update the current task if it has changed
#         if self.current_task != (new_current_product_task.task if new_current_product_task else None):
#             self.current_task = new_current_product_task.task if new_current_product_task else None
#             self.save(update_fields=['current_task'])
        
#         return self.current_task

#     def assign_predefined_tasks_by_status(self):
#         """
#         Assign the predefined tasks of the current status to the product
#         """
#         status_tasks_predefined = self.current_status.status_tasks.filter(is_predefined=True,is_removed = False).order_by('order')
#         product_tasks = [
#             ProductTask(product=self, task=status_task.task, is_predefined=True, is_removed = False)
#             for status_task in status_tasks_predefined
#         ]
#         ProductTask.objects.bulk_create(product_tasks)

#     def assign_tasks(self, task, set_as_predefined_of_status=False):
#         """
#         Assign a task to the product, and update the current task of the product.
#         """
#         with transaction.atomic():
#             # Create a StatusTask for the status and task if necessary
#             StatusTask.objects.get_or_create(
#                 status=self.current_status,
#                 task=task,
#                 defaults={'is_predefined': set_as_predefined_of_status}
#             )
#             # Create a ProductTask for the product
#             ProductTask.objects.get_or_create(product=self, task=task, is_predefined=set_as_predefined_of_status)
#             # Locate the current task of the product
#             self._locate_current_task()


#     def get_all_tasks_of_product(self, only_active=False):
#         """
#         get all the tasks of the product, and return the queryset of the tasks ordered by the created time of the status of the task and the order of the task in the status
#         The instances returned are the instances of the ProductTask model
#         """
#         tasks = self.tasks_of_product.filter(is_removed = False).select_related('task__statustask__status').order_by(
#             'task__statustask__status__created', 'task__statustask__order'
#         )
#         if only_active:
#             tasks = tasks.filter(is_completed=False, is_skipped=False,is_removed = False,)
#         return tasks


#     def get_ongoing_task(self):
#         """
#         get the ongoing task of the product as productTask instance
#         """
#         return self.tasks_of_product.filter(Q(task = self.current_task) 
#                                             & Q(product = self) 
#                                             &  Q(is_completed = False) 
#                                             & Q(is_skipped = False)
#                                             & Q(is_removed = False))
    

#     def list_status_result_history(self):
#         """
#         list the status result history of the product with tasks in all statuses, and return the result as a string
#         """
#         all_product_statuses = self.status_history_of_product.order_by('changed_at')
#         history = [f'Product SN: {self.SN}']
#         for product_status in all_product_statuses:
#             status_result = product_status.get_product_status_result()
#             history.append(f'{status_result} at {product_status.changed_at}')
#         return "\n".join(history)
    
