# apps/finance_app/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum

from .models import Account, Transaction, Budget
from .forms import AccountForm, TransactionForm, BudgetForm
from datetime import timedelta


@login_required
def dashboard(request):
    user = request.user

    # 获取账户信息
    accounts = Account.objects.filter(user=user)
    total_balance = sum(acc.balance for acc in accounts)

    # 获取最近交易
    recent_transactions = Transaction.objects.filter(user=user).order_by('-date')[:5]

    # 计算收入和支出
    total_income = sum(tx.amount for tx in Transaction.objects.filter(user=user, transaction_type='income'))
    total_expense = sum(tx.amount for tx in Transaction.objects.filter(user=user, transaction_type='expense'))

    # 计算预算剩余
    total_budget = sum(b.amount for b in Budget.objects.filter(user=user))
    budget_remaining = total_budget - total_expense

    category_distribution = {}
    expense_txs = Transaction.objects.filter(user=user, transaction_type='expense')
    for tx in expense_txs:
        cat_name = tx.category.name if tx.category else "Others"
        category_distribution[cat_name] = category_distribution.get(cat_name, 0) + float(tx.amount)

    context = {
        'accounts': accounts,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'budget_remaining': budget_remaining,
        # 一定要把这个传给模板
        'category_distribution': category_distribution,
    }
    return render(request, 'finance_app/overview.html', context)



@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'finance_app/transaction_list.html', {'transactions': transactions})

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('finance_app:transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'finance_app/transaction_form.html', {'form': form})

@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('finance_app:transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'finance_app/transaction_form.html', {'form': form})

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('finance_app:transaction_list')
    return render(request, 'finance_app/transaction_confirm_delete.html', {'transaction': transaction})

from django.http import JsonResponse

@login_required
def transaction_filter_ajax(request):
    # 获取前端传递的筛选条件
    category = request.GET.get('category', None)
    transactions = Transaction.objects.filter(user=request.user)
    if category:
        transactions = transactions.filter(category__icontains=category)
    data = []
    for t in transactions:
        data.append({
            'id': t.id,
            'date': t.date.strftime("%Y-%m-%d"),
            'amount': str(t.amount),
            'category': t.category,
            'type': t.transaction_type,
        })
    return JsonResponse({'transactions': data})



@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'finance_app/account_list.html', {'accounts': accounts})

@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect('finance_app:account_list')
    else:
        form = AccountForm()
    return render(request, 'finance_app/account_form.html', {'form': form})

@login_required
def dashboard_filter_ajax(request):
    # 获取前端传来的筛选参数，例如 ?range=this_month
    time_range = request.GET.get('range', 'this_month')
    now = timezone.now()

    # 根据 time_range 不同，计算起止时间
    if time_range == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last_month':
        # 上个月 1 号
        last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        start_date = last_month
    elif time_range == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last_12_months':
        start_date = now - timedelta(days=365)
    else:
        # 默认 this_month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 计算区间：start_date ~ now
    transactions = Transaction.objects.filter(
        user=request.user,
        date__range=(start_date, now)
    )

    total_income = 0
    total_expense = 0
    category_distribution = {}
    expense_txs = Transaction.objects.filter(user=user, transaction_type='expense')
    for tx in expense_txs:
        cat_name = tx.category.name if tx.category else "Others"
        category_distribution[cat_name] = category_distribution.get(cat_name, 0) + float(tx.amount)
    # 最近 5 条交易
    recent_transactions = transactions.order_by('-date')[:5]

    # 组装返回数据
    data = {
        "total_income": total_income,
        "total_expense": total_expense,
        # 这里假设你还要计算 total_balance / budget_remaining 等...
        "category_distribution": category_distribution,
        "recent_transactions": [
            {
                "payee": tx.category,       # 根据需求填“payee”或其他字段
                "category": tx.category,
                "account": tx.account.name,
                "date": tx.date.strftime("%Y-%m-%d"),
                "amount": float(tx.amount),
            }
            for tx in recent_transactions
        ]
    }

    return JsonResponse(data)

@login_required
def add_income(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.transaction_type = 'income'  # 强制设定为收入
            income.save()
            return redirect('finance_app:dashboard')
    else:
        form = TransactionForm(user=request.user)
        # 默认 transaction_type = "income" 已在 form __init__ 里或字段初始值里设定
    return render(request, 'finance_app/add_income.html', {
        'form': form,
        'title': 'Add Income',
    })

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.transaction_type = 'expense'  # 强制设定为支出
            expense.save()
            return redirect('finance_app:dashboard')
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'finance_app/add_expense.html', {
        'form': form,
        'title': 'Add Expense',
    })




@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'finance_app/account_list.html', {'accounts': accounts})

@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect('finance_app:account_list')
    else:
        form = AccountForm()
    return render(request, 'finance_app/account_form.html', {'form': form, 'title': 'Create Account'})

@login_required
def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('finance_app:account_list')
    else:
        form = AccountForm(instance=account)
    return render(request, 'finance_app/account_form.html', {'form': form, 'title': 'Edit Account'})

@login_required
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
        return redirect('finance_app:account_list')
    return render(request, 'finance_app/account_confirm_delete.html', {'account': account})    



@login_required
def analytics(request):
    user = request.user
    now = timezone.now()
    start_date = now - timedelta(days=30)  # 默认最近 30 天
    transactions = Transaction.objects.filter(user=user, date__gte=start_date)

    # 计算收入和支出趋势
    income_data = {}
    expense_data = {}
    category_data = {}

    for tx in transactions:
        date_str = tx.date.date().isoformat()
        if tx.transaction_type == 'income':
            income_data[date_str] = income_data.get(date_str, 0) + float(tx.amount)
        else:
            expense_data[date_str] = expense_data.get(date_str, 0) + float(tx.amount)

        # 计算类别占比
        if tx.category in category_data:
            category_data[tx.category] += float(tx.amount)
        else:
            category_data[tx.category] = float(tx.amount)

    context = {
        'income_data': income_data,
        'expense_data': expense_data,
        'category_data': category_data,
    }
    return render(request, 'finance_app/analytics.html', context)



    
@login_required
def add_transaction(request, tx_type):
    if tx_type not in ['income', 'expense']:
        return redirect('finance_app:dashboard')

    if request.method == 'POST':
        # 这里必须加 transaction_type=tx_type
        form = TransactionForm(request.POST, user=request.user, transaction_type=tx_type)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.transaction_type = tx_type
            tx.save()
            return redirect('finance_app:dashboard')
    else:
        # 这里同样必须加 transaction_type=tx_type
        form = TransactionForm(user=request.user, transaction_type=tx_type)

    context = {
        'form': form,
        'transaction_type': tx_type,
    }
    return render(request, 'finance_app/add_transaction.html', context)



@login_required
def budget_money(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('finance_app:dashboard')
    else:
        form = BudgetForm()
    return render(request, 'finance_app/budget_form.html', {'form': form, 'title': 'Set Budget'})





@login_required
def budget_list(request):
    user = request.user
    budgets = Budget.objects.filter(user=user)

    budget_info_list = []
    for b in budgets:
        # 计算 spent
        expense_qs = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date__range=(b.start_date, b.end_date)
        )
        # 如果 b.account 不为空，就只统计对应 account
        if b.account:
            expense_qs = expense_qs.filter(account=b.account)
        spent = expense_qs.aggregate(total=Sum('amount'))['total'] or 0
        remaining = b.amount - spent
        progress = int((spent / b.amount) * 100) if b.amount > 0 else 0
        budget_info_list.append({
            'budget': b,
            'spent': spent,
            'remaining': remaining,
            'progress': progress,
        })

    return render(request, 'finance_app/budget_list.html', {
        'budget_info_list': budget_info_list
    })



@login_required
def budget_view(request):
    user = request.user
    budgets = Budget.objects.filter(user=user)
    current_month = timezone.now().replace(day=1)

    # 获取每个类别的支出
    expenses_by_category = Transaction.objects.filter(
        user=user, transaction_type="expense", date__gte=current_month
    ).values('category__name').annotate(total_spent=Sum('amount'))

    # 计算预算使用情况
    budget_progress = []
    for budget in budgets:
        spent = next((e['total_spent'] for e in expenses_by_category if e['category__name'] == budget.category.name), 0)
        progress = (spent / budget.amount) * 100 if budget.amount > 0 else 0
        budget_progress.append({
            "category": budget.category.name,
            "budget": budget.amount,
            "spent": spent,
            "progress": min(progress, 100),  # 限制最大100%
            "exceeded": spent > budget.amount
        })

    return render(request, "finance_app/budget.html", {
        "budgets": budgets,
        "budget_progress": budget_progress,
        "form": BudgetForm(),
    })

@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)  # 这里必须传入 user
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user  # 绑定当前用户
            budget.save()
            return redirect('finance_app:budget_view')  # 重定向到预算管理页面
        else:
            print(form.errors)  # 🔴 这一步调试：打印表单错误
    else:
        form = BudgetForm()

    return render(request, 'finance_app/add_budget.html', {'form': form})




