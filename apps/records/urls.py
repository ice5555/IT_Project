# apps/records/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseRecordViewSet, DailyExpenseViewSet, IncomeRecordViewSet

# DRF 路由
router = DefaultRouter()
router.register(r'expense-records', ExpenseRecordViewSet, basename='expense-record')
router.register(r'daily-expenses', DailyExpenseViewSet, basename='daily-expense')
router.register(r'income-records', IncomeRecordViewSet, basename='income-record')
from .views import (
    ExpenseRecordViewSet,
    DailyExpenseViewSet,
    IncomeRecordViewSet,
    add_expense,
    expense_list,
    overview,
    edit_expense,
    delete_expense,
    income_list,
    add_income,
    edit_income,
    delete_income,
    income_category_autocomplete,
    export_expenses,
    import_expenses,
    export_incomes,
    import_incomes,
)

urlpatterns = [
    # DRF 路由
    path('api/', include(router.urls)),

    # 应用的模板视图
    path('add_expense/', add_expense, name='add_expense'),
    path('expenses/', expense_list, name='expense_list'),
    path('overview/', overview, name='overview'),
    path('edit_expense/<int:pk>/', edit_expense, name='edit_expense'),
    path('delete_expense/<int:pk>/', delete_expense, name='delete_expense'),
    path('incomes/', income_list, name='income_list'),
    path('incomes/add/', add_income, name='add_income'),
    path('incomes/edit/<int:pk>/', edit_income, name='edit_income'),
    path('incomes/delete/<int:pk>/', delete_income, name='delete_income'),

    # 自动补全接口
    # path('api/store-autocomplete/', store_autocomplete, name='store_autocomplete'),
    # path('api/product-autocomplete/', product_autocomplete, name='product_autocomplete'),
    path('api/income-category-autocomplete/', income_category_autocomplete, name='income_category_autocomplete'),


    path('export-expenses/', export_expenses, name='export_expenses'),
    path('import-expenses/', import_expenses, name='import_expenses'),
    path('export-incomes/', export_incomes, name='export_incomes'),
    path('import-incomes/', import_incomes, name='import_incomes'),
    
]
