from django.urls import path
from .views import ProductListView, ProductDetailView, ProductTaskView, AddTaskView, StatusTransitionView, home_view
from .views import (
    home_view,
    ProductListView,
    ProductDetailView,
    FeatureManageView,
    CheckinOrUpdateView,
    get_predefined_tasks,
    get_order_choices,
    fetch_categories,
    ManageCategoriesView,
    ManageStatusesView,
    ManageTasksView,
    ManageLocationsView
)

urlpatterns = [
    path('', home_view, name='home'),
    path('products/', ProductListView.as_view(), name='product_list'),
    #path('products/<slug:sn>/', ProductDetailView.as_view(), name='product_detail'),
    path('feature_manage/', FeatureManageView.as_view(), name='feature_manage'),
    path('checkin_or_update/', CheckinOrUpdateView.as_view(), name='checkin_or_update'),
    path('get_predefined_tasks/', get_predefined_tasks, name='get_predefined_tasks'),
    path('get_order_choices/', get_order_choices, name='get_order_choices'),
    path('fetch_categories/', fetch_categories, name='fetch_categories'),
    path('manage_categories/', ManageCategoriesView.as_view(), name='manage_categories'),
    path('manage_statuses/', ManageStatusesView.as_view(), name='manage_statuses'),
    path('manage_tasks/', ManageTasksView.as_view(), name='manage_tasks'),
    path('manage_locations/', ManageLocationsView.as_view(), name='manage_locations'),
    # Other URL patterns
]
