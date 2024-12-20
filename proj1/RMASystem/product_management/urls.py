from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import index
from .views import (
    home_view,
    ProductListView,
    ProductDetailView,
    ProductTaskView,
    AddTaskView,
    StatusTransitionView,
    FeatureManageView,
    get_predefined_tasks,
    get_order_choices,
    fetch_categories,
    get_layers_for_rack,
    get_empty_spaces_for_layer,
    ManageCategoriesView,
    ManageStatusesView,
    ManageTasksView,
    ManageLocationsView,
    CheckinView,
    CheckinNewView,
    UpdateLocationView,
    ViewStatusView,
    SearchLocationView,
    EditStatusOrTaskView,
    CategoryViewSet,
    LocationViewSet,
    StatusViewSet,
    StatusTransitionViewSet,
    StatusTaskViewSet,
    TaskViewSet,
    ProductTaskViewSet,
    ProductStatusViewSet,
    ProductViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'statuses', StatusViewSet)
router.register(r'status-transitions', StatusTransitionViewSet)
router.register(r'status-tasks', StatusTaskViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'product-tasks', ProductTaskViewSet)
router.register(r'product-statuses', ProductStatusViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<str:SN>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<str:SN>/edit/', EditStatusOrTaskView.as_view(), name='edit_status_or_task'),
    path('product-tasks/', ProductTaskView.as_view(), name='product_task'),
    path('add-task/<slug:SN>/', AddTaskView.as_view(), name='add_task'),
    path('status-transition/<int:product_id>/', StatusTransitionView.as_view(), name='status_transition'),

    # URLs for feature management
    path('feature_manage/', FeatureManageView.as_view(), name='feature_manage'),
    path('manage_categories/', ManageCategoriesView.as_view(), name='manage_categories'),
    path('manage_statuses/', ManageStatusesView.as_view(), name='manage_statuses'),
    path('manage_tasks/', ManageTasksView.as_view(), name='manage_tasks'),
    path('manage_locations/', ManageLocationsView.as_view(), name='manage_locations'),
    path('view_status/', ViewStatusView.as_view(), name='view_status'),

    # URLs for checkin or update location
    path('checkin/', CheckinView.as_view(), name='checkin'),
    path('checkin_new/', CheckinNewView.as_view(), name='checkin_new'),
    path('update_location/', UpdateLocationView.as_view(), name='update_location'),

    # URLs for helper views
    path('get_empty_spaces_for_layer/', get_empty_spaces_for_layer, name='get_empty_spaces_for_layer'),
    path('get_predefined_tasks/', get_predefined_tasks, name='get_predefined_tasks'),
    path('get_order_choices/', get_order_choices, name='get_order_choices'),
    path('fetch_categories/', fetch_categories, name='fetch_categories'),
    path('get_layers_for_rack/', get_layers_for_rack, name='get_layers_for_rack'),
    path('search_location/', SearchLocationView.as_view(), name='search_location'),

    # Include the API URLs
    path('api/', include(router.urls)),

    path('', index, name= 'index')
]
