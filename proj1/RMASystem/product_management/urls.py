from django.urls import path
from .views import ProductListView, ProductDetailView, ProductTaskView, AddTaskView, StatusTransitionView, home_view
from .views import (
    home_view,
    ProductListView,
    ProductDetailView,
    FeatureManageView,
    get_predefined_tasks,
    get_order_choices,
    fetch_categories,
    get_layers_for_rack,
    get_spaces_for_layer,
    ManageCategoriesView,
    ManageStatusesView,
    ManageTasksView,
    ManageLocationsView,
    CheckinView,
    CheckinNewView,
    UpdateLocationView,


)

urlpatterns = [
    path('', home_view, name='home'),
    path('products/', ProductListView.as_view(), name='product_list'),
    
    #urls for feature management
    path('feature_manage/', FeatureManageView.as_view(), name='feature_manage'),

    path('manage_categories/', ManageCategoriesView.as_view(), name='manage_categories'),
    path('manage_statuses/', ManageStatusesView.as_view(), name='manage_statuses'),
    path('manage_tasks/', ManageTasksView.as_view(), name='manage_tasks'),
    path('manage_locations/', ManageLocationsView.as_view(), name='manage_locations'),
    # urls for checkin or update location
    path('checkin/', CheckinView.as_view(), name='checkin'),
    path('checkin_new/', CheckinNewView.as_view(), name='checkin_new'),
    path('update_location/', UpdateLocationView.as_view(), name='update_location'),
    

    # urls for helper views
    path('get_spaces_for_layer/', get_spaces_for_layer, name='get_spaces_for_layer'),
    path('get_predefined_tasks/', get_predefined_tasks, name='get_predefined_tasks'),
    path('get_order_choices/', get_order_choices, name='get_order_choices'),
    path('fetch_categories/', fetch_categories, name='fetch_categories'),
    path('get_layers_for_rack/', get_layers_for_rack, name='get_layers_for_rack'),
]
