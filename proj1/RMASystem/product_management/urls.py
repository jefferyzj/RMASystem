from django.urls import path
from .views import ProductListView, ProductDetailView, ProductTaskView, AddTaskView, StatusTransitionView, home_view
from .views import (
    home_view,
    ProductListView,
    ProductDetailView,
    FeatureManageView,
    CheckinOrUpdateView,
)
urlpatterns = [
    path('', home_view, name='home'),
    path('products/', ProductListView.as_view(), name='product_list'),
    #path('products/<slug:sn>/', ProductDetailView.as_view(), name='product_detail'),
    path('feature_manage/', FeatureManageView.as_view(), name='feature_manage'),
    path('checkin_or_update/', CheckinOrUpdateView.as_view(), name='checkin_or_update'),
    # Other URL patterns
]
