
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
    #4. add functionality to add status with next possible status, and the status transition.
"""
Things about feature_manage:

Categories:

Add Category: Allow the user to input a category name and save it.
Delete Category: Allow the user to select an existing category from a dropdown list, which includes the count of products belonging to each category. If the number of products belonging to the category is not zero, show a message when the user tries to delete the category.

Tasks:

Add Task: Allow the user to create a new task with fields for action, description, status (optional), predefined status (optional), and order (optional).
Delete Task: Allow the user to delete existing tasks.
Predefined Tasks: If a task is mapped to a status and set as predefined, the user must specify an order for the predefined task.

Statuses:

Add Status: Allow the user to create a new status with fields for name, description, and whether it is a closed status.
Delete Status: Allow the user to delete existing statuses.

Locations:

Add Location: Allow the user to create new locations with fields for rack name, layer number, and number of spaces per layer.
Remove Location: Allow the user to remove existing locations by specifying the rack name and layer number. Ensure that locations storing products cannot be removed.
"""