# apps/records/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, Value, DecimalField, F
from django.db.models.functions import Upper, Trim
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import ExpenseRecord, DailyExpense, IncomeRecord, CURRENCY_SYMBOLS
from .serializers import ExpenseRecordSerializer, DailyExpenseSerializer, IncomeRecordSerializer
from .forms import ExpenseRecordForm, IncomeRecordForm

import logging
import csv

from datetime import datetime

logger = logging.getLogger(__name__)

# ExpenseRecord ViewSet
class ExpenseRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseRecordSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.generate_daily_expenses()

    def get_queryset(self):
        return ExpenseRecord.objects.filter(user=self.request.user)
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
            'tags','description', 'specification', 'category', 'original_price', 'current_price', 'discount_type', 'store', 'estimated_usage_days',
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
    permission_classes = [IsAuthenticated]
    serializer_class = DailyExpenseSerializer

    def get_queryset(self):
        return DailyExpense.objects.filter(expense_record__user=self.request.user)
# IncomeRecord ViewSet

class IncomeRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = IncomeRecordSerializer

    def get_queryset(self):
        return IncomeRecord.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有收入类别，用于前端自动补全"""
        categories = IncomeRecord.objects.values_list('category', flat=True).distinct()
        return Response(list(categories), status=status.HTTP_200_OK)



# 视图函数部分
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseRecordForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense = form.save()
            expense.generate_daily_expenses()
            return redirect('expense_list')
    else:
        form = ExpenseRecordForm()
    return render(request, 'records/add_expense.html', {'form': form})

@login_required
def expense_list(request):
    expenses = ExpenseRecord.objects.filter(user=request.user).order_by('-purchase_date')
    context = {'expenses': expenses}
    return render(request, 'records/expense_list.html', context)

@login_required
def overview(request):
    # 获取所有使用的货币
    income_currencies = IncomeRecord.objects.values_list('currency', flat=True).distinct()
    expense_currencies = ExpenseRecord.objects.values_list('currency', flat=True).distinct()
    currencies = set(list(income_currencies) + list(expense_currencies))

    # 初始化存储数据的字典
    currency_data = {}

    for currency in currencies:
        # 计算收入和支出
        total_income = IncomeRecord.objects.filter(currency=currency).aggregate(total=Sum('amount'))['total'] or 0
        total_expense = ExpenseRecord.objects.filter(currency=currency).aggregate(total=Sum('current_price'))['total'] or 0
        net_balance = total_income - total_expense

        # 分类统计
        expense_by_category = ExpenseRecord.objects.filter(currency=currency).values('category').annotate(total=Sum('current_price'))
        income_by_category = IncomeRecord.objects.filter(currency=currency).values('category').annotate(total=Sum('amount'))

        # 获取货币符号
        currency_symbol = CURRENCY_SYMBOLS.get(currency, '')

        # 存储数据
        currency_data[currency] = {
            'currency_symbol': currency_symbol,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_balance': net_balance,
            'expense_by_category': expense_by_category,
            'income_by_category': income_by_category,
        }

    context = {
        'currency_data': currency_data,
    }

    return render(request, 'records/overview.html', context)

@login_required
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

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('expense_list')
    return render(request, 'records/delete_expense.html', {'expense': expense})

# 自动补全接口
@login_required
def store_autocomplete(request):
    query = request.GET.get('q', '')
    stores = ExpenseRecord.objects.filter(store__icontains=query).values_list('store', flat=True).distinct()
    return JsonResponse(list(stores), safe=False)


@login_required
def income_list(request):
    # 获取所有类别，用于筛选
    categories = IncomeRecord.objects.filter(user=request.user).values_list('category', flat=True).distinct()
    
    # 获取用户选择的筛选条件
    selected_category = request.GET.get('category')

    # 查询实际收入（已完成）
    actual_incomes = IncomeRecord.objects.filter(user=request.user, status='completed')
    if selected_category:
        actual_incomes = actual_incomes.filter(category=selected_category)
    
    # 查询预计收入（未完成或未支付）
    expected_incomes = IncomeRecord.objects.filter(user=request.user).exclude(status='completed')
    if selected_category:
        expected_incomes = expected_incomes.filter(category=selected_category)
    
    # 计算已完成收入总额（按货币分组）
    actual_totals = actual_incomes.values('currency').annotate(
        total=Sum(Case(
            When(amount__isnull=False, then=F('amount')),
            default=Value(0),
            output_field=DecimalField()
        ))
    )
    
    # 计算未支付收入总额（按货币分组）
    unpaid_totals = IncomeRecord.objects.filter(
        user=request.user, status='unpaid'
    ).values('currency').annotate(
        total=Sum(Case(
            When(expected_amount__isnull=False, then=F('expected_amount')),
            default=Value(0),
            output_field=DecimalField()
        ))
    )

    # 计算未完成收入总额（按货币分组）
    pending_totals = IncomeRecord.objects.filter(
        user=request.user, status='pending'
    ).values('currency').annotate(
        total=Sum(Case(
            When(expected_amount__isnull=False, then=F('expected_amount')),
            default=Value(0),
            output_field=DecimalField()
        ))
    )

    # 将查询结果转换为字典格式
    actual_totals_dict = {item['currency']: item['total'] or 0 for item in actual_totals}
    unpaid_totals_dict = {item['currency']: item['total'] or 0 for item in unpaid_totals}
    pending_totals_dict = {item['currency']: item['total'] or 0 for item in pending_totals}

    context = {
        'categories': categories,
        'selected_category': selected_category,
        'actual_incomes': actual_incomes.order_by('-date'),
        'expected_incomes': expected_incomes.order_by('ddl'),
        'actual_totals': actual_totals_dict,
        'unpaid_totals': unpaid_totals_dict,
        'pending_totals': pending_totals_dict,
    }
    
    return render(request, 'records/income_list.html', context)

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeRecordForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            form.save()
            return redirect('income_list')
    else:
        form = IncomeRecordForm()
    return render(request, 'records/add_income.html', {'form': form})

@login_required
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

@login_required
def delete_income(request, pk):
    income = get_object_or_404(IncomeRecord, pk=pk)
    if request.method == 'POST':
        income.delete()
        return redirect('income_list')
    return render(request, 'records/delete_income.html', {'income': income})

@login_required
def income_category_autocomplete(request):
    query = request.GET.get('q', '')
    categories = IncomeRecord.objects.filter(category__icontains=query).values_list('category', flat=True).distinct()
    return JsonResponse(list(categories), safe=False)



@login_required
def export_expenses(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Description', 'Specification', 'Category', 'Tags', 'Original Price', 'Current Price',
                     'Discount Type', 'Store', 'Estimated Usage Days', 'Purchase Date', 'Expiration Date'])

    expenses = ExpenseRecord.objects.filter(user=request.user)
    for expense in expenses:
        writer.writerow([
            expense.description,
            expense.specification,
            expense.category,
            expense.tags,
            expense.original_price,
            expense.current_price,
            expense.discount_type,
            expense.store,
            expense.estimated_usage_days,
            expense.purchase_date,
            expense.expiration_date,
        ])

    return response


# 导出收入记录为 CSV
@login_required
def export_incomes(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="incomes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Source', 'Amount', 'Category', 'Date', 'Tags'])

    incomes = IncomeRecord.objects.filter(user=request.user)
    for income in incomes:
        writer.writerow([
            income.source,
            income.amount,
            income.category,
            income.date,
            income.tags,
        ])

    return response


# 导入支出记录
@login_required
def import_expenses(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        next(reader)  # 跳过表头

        for row in reader:
            ExpenseRecord.objects.create(
                user=request.user,
                description=row[0],
                specification=row[1],
                category=row[2],
                tags=row[3],
                original_price=row[4],
                current_price=row[5],
                discount_type=row[6],
                store=row[7],
                estimated_usage_days=row[8],
                purchase_date=row[9],
                expiration_date=row[10] if row[10] else None
            )
        return redirect('expense_list')

    return render(request, 'records/import_expenses.html')


# 导入收入记录
@login_required
def import_incomes(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        next(reader)  # 跳过表头

        for row in reader:
            IncomeRecord.objects.create(
                user=request.user,
                source=row[0],
                amount=row[1],
                category=row[2],
                date=row[3],
                tags=row[4]
            )
        return redirect('income_list')

    return render(request, 'records/import_incomes.html')
