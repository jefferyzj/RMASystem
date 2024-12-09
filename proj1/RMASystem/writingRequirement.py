
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
    #5 12/2, add task is generally done, but need to take care of insert the statustask created with an order, the save() method of statustask still need to develop
    #6 12/2 night/ finishe the add task part, but have not test it fully. Handle three case of add task.  still need to take care of delete task.
    
    #7 12/6 finish the manage status part, but can still develop its UI, and need to test it.
    #8 12/6 consider to use soft delete for status, task, and some other models. Since we may need to delete status sometimes, but we don't want to loss the data like in productstatus, statusTask, and so on.
    #9 12/9 finish the manage location part, but need to test it.
    #10 12/9 almost finish the manage feature part. Need to add some update action to the task and status part.
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

"""
requirements to add task:

Add a single task without mapping to a status.
Add a task and a StatusTask with mapping to a status and set it as non-predefined.
Automatically assign this StatusTask to the tail of the order of all StatusTask instances with respect to the status.
Add a predefined task of a status with an order.
Ensure predefined tasks always stand at the head of the order.
Allow the user to insert the predefined task at a specific position among the predefined tasks or at the tail of the predefined tasks.
"""

"""
Requirement about status manage:
Add Status:

The user must provide a name for the status.
There is a checkbox to indicate if it is a closed status.
There is a field as a checkbox named "Possible Next Statuses" allowing the user to select multiple possible next statuses of the new status from the existing statuses.
This field is optional.
In this process, it will create StatusTransition instances to remember this mapping.
Delete Status:

The user can delete an existing status.
The deletion should be handled separately from the addition/updating of statuses.
"""

"""
Requirements for Manage Location Page
Page Structure:

The page should have two parts: add location and delete location.
When the user clicks on manage location, it should navigate to the manage_location page.
The user should see two radio buttons: add location and delete location.
The user should see existing racks and the number of products belonging to each rack, including information about all layers of each rack.
For each rack, it should show how many locations are occupied by a product.
Add Location:

The user should enter the rack name and layer number.
Optionally, the user can enter the number of spaces to create multiple locations.
If only the rack name and layer number are provided, the default number of spaces should be set to 60.
Create 60 location instances with the product attribute set to null if the number of spaces is not specified.
Delete Location:

The user should select from the existing rack names.
The user should select from the layers existing in the selected rack.
The user can only delete a layer of a rack if all locations on that layer are not storing products.
Style:

The manage location page should follow the style of the manage tasks page.
"""