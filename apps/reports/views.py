import matplotlib.pyplot as plt
import io
import base64
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from ..records.models import ExpenseRecord, IncomeRecord
from django.utils import timezone
from datetime import datetime, timedelta

def generate_pie_chart(data, labels):
    """生成支出按类别的饼图"""
    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # 确保饼图为圆形

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def overview_charts(request):
    # 收入和支出总览
    total_income = float(IncomeRecord.objects.aggregate(total=Sum('amount'))['total'] or 0)
    total_expense = float(ExpenseRecord.objects.aggregate(total=Sum('current_price'))['total'] or 0)
    net_balance = total_income - total_expense

    # 支出按类别
    expenses_by_category = ExpenseRecord.objects.values('category').annotate(total=Sum('current_price'))
    categories = [item['category'] for item in expenses_by_category]
    category_totals = [float(item['total']) for item in expenses_by_category]

    # 获取过去 12 个月的月度收入和支出数据
    today = timezone.now()
    start_date = today - timedelta(days=365)

    # 按月份聚合收入数据
    income_by_month = (
        IncomeRecord.objects
        .filter(date__gte=start_date)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    
    # 按月份聚合支出数据
    expense_by_month = (
        ExpenseRecord.objects
        .filter(purchase_date__gte=start_date)
        .annotate(month=TruncMonth('purchase_date'))
        .values('month')
        .annotate(total=Sum('current_price'))
        .order_by('month')
    )

    # 准备数据以供 Chart.js 使用
    monthly_labels = [item['month'].strftime('%Y-%m') for item in income_by_month]
    monthly_income_data = [float(item['total']) for item in income_by_month]
    monthly_expense_data = [float(item['total']) for item in expense_by_month]

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'category_data': category_totals,
        'category_labels': categories,
        'monthly_labels': monthly_labels,
        'monthly_data': {
            'income': monthly_income_data,
            'expense': monthly_expense_data,
        }
    }
    return render(request, 'reports/overview_charts.html', context)