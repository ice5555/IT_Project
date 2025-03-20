import matplotlib.pyplot as plt
import io
import base64
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDay

from ..records.models import Transaction, CURRENCY_SYMBOLS
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
    # Get list of currencies used in income and expense records
    income_currencies = IncomeRecord.objects.values_list('currency', flat=True).distinct()
    expense_currencies = ExpenseRecord.objects.values_list('currency', flat=True).distinct()
    currencies = set(list(income_currencies) + list(expense_currencies))

    currency_data = {}

    for currency in currencies:
        # Income and expense totals per currency
        total_income = IncomeRecord.objects.filter(currency=currency).aggregate(total=Sum('amount'))['total'] or 0
        total_expense = ExpenseRecord.objects.filter(currency=currency).aggregate(total=Sum('current_price'))['total'] or 0
        net_balance = total_income - total_expense

        # Expenses by category per currency
        expenses_by_category = ExpenseRecord.objects.filter(currency=currency).values('category').annotate(total=Sum('current_price'))
        categories = [item['category'] for item in expenses_by_category]
        category_totals = [float(item['total'] or 0) for item in expenses_by_category]

        # Monthly income and expense data per currency
        today = timezone.now()
        start_date = today - timedelta(days=365)

        income_by_month = (
            IncomeRecord.objects
            .filter(date__gte=start_date, currency=currency)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        expense_by_month = (
            ExpenseRecord.objects
            .filter(purchase_date__gte=start_date, currency=currency)
            .annotate(month=TruncMonth('purchase_date'))
            .values('month')
            .annotate(total=Sum('current_price'))
            .order_by('month')
        )

        monthly_labels = [item['month'].strftime('%Y-%m') for item in income_by_month]
        monthly_income_data = [float(item['total'] or 0) for item in income_by_month]
        monthly_expense_data = [float(item['total'] or 0) for item in expense_by_month]

        currency_symbol = CURRENCY_SYMBOLS.get(currency, '')

        currency_data[currency] = {
            'currency_symbol': currency_symbol,
            'total_income': float(total_income or 0),
            'total_expense': float(total_expense or 0),
            'net_balance': float(net_balance or 0),
            'category_data': category_totals,
            'category_labels': categories,
            'monthly_labels': monthly_labels,
            'monthly_income_data': monthly_income_data,
            'monthly_expense_data': monthly_expense_data,
        }

    context = {
        'currency_data': currency_data,
    }

    return render(request, 'reports/overview_charts.html', context)



@login_required
def income_trend_chart(request):
    # 获取查询参数
    source = request.GET.get('source')
    category = request.GET.get('category')
    days = int(request.GET.get('days', 30))  # 默认为30天

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # 筛选数据
    incomes = IncomeRecord.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    )

    if source:
        incomes = incomes.filter(source=source)
    if category:
        incomes = incomes.filter(category=category)

    # 按天聚合收入数据
    income_by_day = incomes.annotate(day=TruncDay('date')).values('day').annotate(total=Sum('amount')).order_by('day')

    # 准备数据供前端使用
    labels = [entry['day'].strftime('%Y-%m-%d') for entry in income_by_day]
    data = [float(entry['total']) for entry in income_by_day]

    return JsonResponse({'labels': labels, 'data': data})

@login_required
def income_list(request):
    sources = IncomeRecord.objects.values_list('source', flat=True).distinct()
    categories = IncomeRecord.objects.values_list('category', flat=True).distinct()
    
    context = {
        'sources': sources,
        'categories': categories,
    }
    return render(request, 'reports/income_list.html', context)
