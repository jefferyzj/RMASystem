from django.urls import path
from .views import ProductListView, ProductDetailView, ProductUpdateView, ProductTaskView, AddTaskView, StatusTransitionView

urlpatterns = [
    path('products/', ProductListView.as_view(), name='products'),
    path('products/<str:sn>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<str:sn>/edit/', ProductUpdateView.as_view(), name='edit_product'),
    path('products/<str:sn>/task/', ProductTaskView.as_view(), name='product_task'),
    path('task/<int:task_id>/edit/', ProductTaskView.as_view(), name='edit_task'),
    path('task/<int:task_id>/skip/', ProductTaskView.as_view(), name='skip_task'),
    path('products/<str:sn>/add_task/', AddTaskView.as_view(), name='add_task'),
    path('products/<int:product_id>/transition/', StatusTransitionView.as_view(), name='transition_status'),
    # Other URL patterns
]
