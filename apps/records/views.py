# apps/records/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import ExpenseRecord, DailyExpense, IncomeRecord
from .serializers import ExpenseRecordSerializer, DailyExpenseSerializer, IncomeRecordSerializer
from .forms import ExpenseRecordForm, IncomeRecordForm

import logging

logger = logging.getLogger(__name__)

# ExpenseRecord ViewSet
class ExpenseRecordViewSet(viewsets.ModelViewSet):
    queryset = ExpenseRecord.objects.all()
    serializer_class = ExpenseRecordSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.generate_daily_expenses()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.update_daily_expenses()
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """列表视图，附带缓存控制"""
        response = super().list(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有类别，用于前端自动补全"""
        categories = ExpenseRecord.objects.values_list('category', flat=True).distinct()
        return Response(list(categories), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def mark_as_used(self, request, pk=None):
        """标记物品为已用尽，并调整每日开销"""
        expense = self.get_object()
        actual_days = request.data.get('actual_usage_days')

        if actual_days:
            expense.actual_usage_days = int(actual_days)
            expense.save()
            expense.update_daily_expenses()
            return Response({"message": "已成功更新使用天数和每日开销"}, status=status.HTTP_200_OK)
        return Response({"error": "缺少实际使用天数"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def batch_update_expiration(self, request):
        """批量更新过期日期"""
        ids = request.data.get('ids', [])
        new_date = request.data.get('expiration_date')
        ExpenseRecord.objects.filter(id__in=ids).update(expiration_date=new_date)
        return Response({"message": "批量更新成功"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def batch_update_purchase(self, request):
        """批量更新购买日期"""
        ids = request.data.get('ids', [])
        new_purchase_date = request.data.get('purchase_date', None)

        if not ids or not new_purchase_date:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_purchase_date = datetime.strptime(new_purchase_date, '%Y-%m-%d').date()
            ExpenseRecord.objects.filter(id__in=ids).update(purchase_date=new_purchase_date)
            return Response({"message": "Purchase dates updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def store_autocomplete(self, request):
        """获取购买地点自动补全建议"""
        query = request.query_params.get('q', '')
        stores = ExpenseRecord.objects.filter(store__icontains=query).values_list('store', flat=True).distinct()
        return Response(list(stores), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def product_autocomplete(self, request):
        """获取商品自动补全建议"""
        query = request.query_params.get('q', '')
        products = ExpenseRecord.objects.filter(description__icontains=query).values(
            'description', 'specification', 'category', 'original_price', 'current_price', 'discount_type', 'store'
        ).distinct()
        return Response(list(products), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """获取本月支出总结"""
        today = timezone.now()
        start_of_month = today.replace(day=1)
        records = ExpenseRecord.objects.filter(purchase_date__gte=start_of_month)
        total_expense = records.aggregate(total=Sum('current_price'))['total'] or 0
        category_expenses = records.values('category').annotate(total=Sum('current_price'))
        return Response({
            "total_expense": total_expense,
            "category_expenses": list(category_expenses)
        })

# DailyExpense ViewSet
class DailyExpenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyExpense.objects.all()
    serializer_class = DailyExpenseSerializer

# IncomeRecord ViewSet
class IncomeRecordViewSet(viewsets.ModelViewSet):
    queryset = IncomeRecord.objects.all()
    serializer_class = IncomeRecordSerializer

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有收入类别，用于前端自动补全"""
        categories = IncomeRecord.objects.values_list('category', flat=True).distinct()
        return Response(list(categories), status=status.HTTP_200_OK)



# 视图函数部分
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseRecordForm(request.POST)
        if form.is_valid():
            expense = form.save()
            expense.generate_daily_expenses()
            return redirect('expense_list')
    else:
        form = ExpenseRecordForm()
    return render(request, 'records/add_expense.html', {'form': form})

def expense_list(request):
    expenses = ExpenseRecord.objects.all().order_by('-purchase_date')
    context = {'expenses': expenses}
    return render(request, 'records/expense_list.html', context)

def overview(request):
    total_income = IncomeRecord.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = ExpenseRecord.objects.aggregate(total=Sum('current_price'))['total'] or 0
    net_balance = total_income - total_expense

    expense_by_category = ExpenseRecord.objects.values('category').annotate(total=Sum('current_price'))
    income_by_category = IncomeRecord.objects.values('category').annotate(total=Sum('amount'))

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,
    }

    return render(request, 'records/overview.html', context)

def edit_expense(request, pk):
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    if request.method == 'POST':
        form = ExpenseRecordForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save()
            expense.update_daily_expenses()
            return redirect('expense_list')
    else:
        form = ExpenseRecordForm(instance=expense)
    return render(request, 'records/edit_expense.html', {'form': form})

def delete_expense(request, pk):
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('expense_list')
    return render(request, 'records/delete_expense.html', {'expense': expense})

# 自动补全接口
def store_autocomplete(request):
    query = request.GET.get('q', '')
    stores = ExpenseRecord.objects.filter(store__icontains=query).values_list('store', flat=True).distinct()
    return JsonResponse(list(stores), safe=False)

def product_autocomplete(request):
    query = request.GET.get('q', '')
    products = ExpenseRecord.objects.filter(description__icontains=query).values('description').distinct()
    descriptions = [item['description'] for item in products]
    return JsonResponse(descriptions, safe=False)

def income_list(request):
    incomes = IncomeRecord.objects.all().order_by('-date')
    context = {'incomes': incomes}
    return render(request, 'records/income_list.html', context)

def add_income(request):
    if request.method == 'POST':
        form = IncomeRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('income_list')
    else:
        form = IncomeRecordForm()
    return render(request, 'records/add_income.html', {'form': form})

def edit_income(request, pk):
    income = get_object_or_404(IncomeRecord, pk=pk)
    if request.method == 'POST':
        form = IncomeRecordForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            return redirect('income_list')
    else:
        form = IncomeRecordForm(instance=income)
    return render(request, 'records/edit_income.html', {'form': form})

def delete_income(request, pk):
    income = get_object_or_404(IncomeRecord, pk=pk)
    if request.method == 'POST':
        income.delete()
        return redirect('income_list')
    return render(request, 'records/delete_income.html', {'income': income})

def income_category_autocomplete(request):
    query = request.GET.get('q', '')
    categories = IncomeRecord.objects.filter(category__icontains=query).values_list('category', flat=True).distinct()
    return JsonResponse(list(categories), safe=False)
