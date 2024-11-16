# apps/records/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF 路由
router = DefaultRouter()
router.register(r'expense-records', views.ExpenseRecordViewSet, basename='expense-record')
router.register(r'daily-expenses', views.DailyExpenseViewSet, basename='daily-expense')
router.register(r'income-records', views.IncomeRecordViewSet, basename='income-record')

urlpatterns = [
    # DRF 路由
    path('api/', include(router.urls)),

    # 应用的模板视图
    path('add_expense/', views.add_expense, name='add_expense'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('overview/', views.overview, name='overview'),
    path('edit_expense/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete_expense/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('incomes/', views.income_list, name='income_list'),
    path('incomes/add/', views.add_income, name='add_income'),
    path('incomes/edit/<int:pk>/', views.edit_income, name='edit_income'),
    path('incomes/delete/<int:pk>/', views.delete_income, name='delete_income'),

    # 自动补全接口
    path('api/store-autocomplete/', views.store_autocomplete, name='store_autocomplete'),
    path('api/product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),
    path('api/income-category-autocomplete/', views.income_category_autocomplete, name='income_category_autocomplete'),
    
]
