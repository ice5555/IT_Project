# apps/records/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

# DRF 路由
router = DefaultRouter()
from .views import (
    transaction_list, add_transaction, edit_transaction, delete_transaction,
    export_transactions, import_transactions
)

urlpatterns = [
    # DRF 路由
    path('api/', include(router.urls)),
    # 应用的模板视图
    path('', transaction_list, name='transaction_list'),
    path('add/', add_transaction, name='add_transaction'),
    path('<int:pk>/edit/', edit_transaction, name='edit_transaction'),
    path('<int:pk>/delete/', delete_transaction, name='delete_transaction'),
    path('export/', export_transactions, name='export_transactions'),
    path('import/', import_transactions, name='import_transactions'),

    # 自动补全接口
    # path('api/store-autocomplete/', store_autocomplete, name='store_autocomplete'),
    # path('api/product-autocomplete/', product_autocomplete, name='product_autocomplete'),


]
