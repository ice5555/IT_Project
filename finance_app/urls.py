# apps/user_auth/urls.py

from django.urls import path
from . import views

app_name = 'finance_app'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/filter_ajax/', views.dashboard_filter_ajax, name='dashboard_filter_ajax'),
    path('transactions/add_income/', views.add_income, name='add_income'),
    path('transactions/add_expense/', views.add_expense, name='add_expense'),
    path('budget/set/', views.budget_money, name='budget_money'),
    
    path('budget/', views.budget_view, name='budget_view'),  # 预算主页
    path('budget/add/', views.add_budget, name='add_budget'),  # 添加预算


    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
path('accounts/<int:account_id>/', views.account_detail, name='account_detail'),

    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    path('analytics/', views.analytics, name='analytics'),

    path('add-transaction/<str:tx_type>/', views.add_transaction, name='add_transaction'),
path('transaction/detail/<int:pk>/', views.transaction_detail, name='transaction_detail'),
path('transactions/export/csv/', views.export_transactions_csv, name='export_transactions_csv'),
path('transactions/export/json/', views.export_transactions_json, name='export_transactions_json'),
path('transactions/import/', views.import_transactions_csv, name='import_transactions_csv'),

    # AJAX
    path('transactions/filter_ajax/', views.dashboard_filter_ajax, name='dashboard_filter_ajax'),
]