# apps/finance_app/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.http import JsonResponse

from .models import Account, Transaction, Budget
from .forms import AccountForm, TransactionForm, BudgetForm
from datetime import timedelta
import csv

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
def dashboard_filter_ajax(request):
    # 获取当前用户
    user = request.user

    # 获取前端传来的时间筛选参数，例如 ?range=this_month
    time_range = request.GET.get('range', 'this_month')
    now = timezone.now()

    # 根据 time_range 计算起始日期
    if time_range == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last_month':
        last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        start_date = last_month
    elif time_range == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last_12_months':
        start_date = now - timedelta(days=365)
    else:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 筛选指定日期范围内的交易记录
    transactions = Transaction.objects.filter(user=user, date__range=(start_date, now))

    # 计算总收入和总支出
    total_income = sum(tx.amount for tx in transactions if tx.transaction_type == 'income')
    total_expense = sum(tx.amount for tx in transactions if tx.transaction_type == 'expense')

    # 计算每个类别的支出总额
    category_distribution = {}
    for tx in transactions:
        if tx.transaction_type == 'expense':
            cat_name = tx.category.name if tx.category else "Others"
            category_distribution[cat_name] = category_distribution.get(cat_name, 0) + float(tx.amount)

    # 取最近 5 条交易记录
    recent_transactions = transactions.order_by('-date')[:5]
    recent_tx_list = []
    for tx in recent_transactions:
        recent_tx_list.append({
            "payee": tx.category.name if tx.category else "N/A",  # 可以根据需求调整显示内容
            "category": tx.category.name if tx.category else "N/A",
            "account": tx.account.name,
            "date": tx.date.strftime("%Y-%m-%d"),
            "amount": float(tx.amount),
        })

    data = {
        "total_income": total_income,
        "total_expense": total_expense,
        "category_distribution": category_distribution,
        "recent_transactions": recent_tx_list,
    }
    return JsonResponse(data)


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

@login_required
def export_transactions_csv(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user).order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Date', 'Type', 'Category', 'Account', 'Amount', 'Note'])
    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.date.strftime("%Y-%m-%d"),
            tx.get_transaction_type_display(),
            tx.category.name if tx.category else '',
            tx.account.name,
            tx.amount,
            tx.note,
        ])

    return response
    
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
def transaction_list_filter(request):
    user = request.user
    # 初始查询条件：当前用户的交易记录
    qs = Transaction.objects.filter(user=user).order_by('-date')

    # 获取过滤参数
    account_id = request.GET.get('account')
    category_id = request.GET.get('category')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 按账户过滤
    if account_id:
        qs = qs.filter(account__id=account_id)
    # 按类别过滤
    if category_id:
        qs = qs.filter(category__id=category_id)
    # 按金额范围过滤
    if min_amount:
        qs = qs.filter(amount__gte=min_amount)
    if max_amount:
        qs = qs.filter(amount__lte=max_amount)
    # 按日期范围过滤
    if start_date:
        qs = qs.filter(date__date__gte=start_date)
    if end_date:
        qs = qs.filter(date__date__lte=end_date)

    context = {
        'transactions': qs,
    }
    return render(request, 'finance_app/transaction_list.html', context)

@login_required
def export_transactions_json(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user).order_by('-date')
    data = []
    for tx in transactions:
        data.append({
            'id': tx.id,
            'date': tx.date.strftime("%Y-%m-%d"),
            'type': tx.get_transaction_type_display(),
            'category': tx.category.name if tx.category else '',
            'account': tx.account.name,
            'amount': float(tx.amount),
            'note': tx.note,
        })
    return JsonResponse(data, safe=False)
@login_required
def transaction_detail(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    html = render_to_string("finance_app/transaction_detail.html", {"transaction": tx})
    return HttpResponse(html)
@login_required
def export_transactions_json(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user).order_by('-date')
    data = []
    for tx in transactions:
        data.append({
            'id': tx.id,
            'date': tx.date.strftime("%Y-%m-%d"),
            'type': tx.get_transaction_type_display(),
            'category': tx.category.name if tx.category else '',
            'account': tx.account.name,
            'amount': float(tx.amount),
            'note': tx.note,
        })
    return JsonResponse(data, safe=False)

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
def import_transactions_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        file_data = csv_file.read().decode("utf-8")
        csv_data = csv.reader(StringIO(file_data))
        # 跳过标题行
        next(csv_data, None)
        for row in csv_data:
            # 假设 CSV 每行格式: ID, Date, Type, Category, Account, Amount, Note
            # 你可以忽略 ID
            date_str = row[1]
            tx_type = row[2].lower()  # 'income' or 'expense'
            category_name = row[3]
            account_name = row[4]
            amount = row[5]
            note = row[6]
            # 根据 account_name 查找 Account 对象（确保当前用户下有这个账户）
            account = Account.objects.filter(user=request.user, name=account_name).first()
            # 根据 category_name 查找 Category 对象
            category = Category.objects.filter(name=category_name).first()

            # 创建交易
            Transaction.objects.create(
                user=request.user,
                account=account,
                amount=amount,
                category=category,
                date=date_str,
                note=note,
                transaction_type=tx_type
            )
        return redirect('finance_app:transaction_list')
    return render(request, 'finance_app/import_transactions.html')


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
def account_detail(request, account_id):
    account = get_object_or_404(Account, id=account_id, user=request.user)
    transactions = Transaction.objects.filter(user=request.user, account=account).order_by('-date')
    return render(request, 'finance_app/account_detail.html', {
        'account': account,
        'transactions': transactions,
    })

@login_required
def analytics(request):
    user = request.user
    now = timezone.now()
    start_date = now - timedelta(days=30)  # 统计最近 30 天数据

    # 1. 收支趋势图数据：按日期汇总收入与支出
    transactions = Transaction.objects.filter(user=user, date__gte=start_date)
    # 构造日期列表（格式 YYYY-MM-DD）
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
    income_trend = {d: 0 for d in dates}
    expense_trend = {d: 0 for d in dates}
    for tx in transactions:
        d = tx.date.date().strftime("%Y-%m-%d")
        if tx.transaction_type == 'income':
            income_trend[d] += float(tx.amount)
        else:
            expense_trend[d] += float(tx.amount)

    # 2. 类别占比数据（仅支出）
    expense_qs = Transaction.objects.filter(user=user, transaction_type='expense', date__gte=start_date)
    category_distribution = {}
    for tx in expense_qs:
        cat_name = tx.category.name if tx.category else "Others"
        category_distribution[cat_name] = category_distribution.get(cat_name, 0) + float(tx.amount)

    # 3. 各账户余额变化（简单计算示例）
    # 这里我们假设：账户余额变化 = 当前余额 - 过去30天内该账户所有交易的总变动（收入正，支出负）
    account_data = {}
    accounts = Account.objects.filter(user=user)
    for account in accounts:
        txs = Transaction.objects.filter(user=user, account=account, date__gte=start_date)
        change = 0
        for tx in txs:
            if tx.transaction_type == 'income':
                change += float(tx.amount)
            else:
                change -= float(tx.amount)
        # 假设初始余额 30 天前 = 当前余额 - change
        initial_balance = float(account.balance) - change
        # 构造时间序列：这里用两点表示：30 天前和现在
        account_data[account.name] = {
            "initial": initial_balance,
            "current": float(account.balance)
        }

    context = {
        "income_trend_dates": list(income_trend.keys()),
        "income_trend_values": list(income_trend.values()),
        "expense_trend_values": list(expense_trend.values()),
        "category_distribution": category_distribution,
        "account_data": account_data,
    }
    return render(request, "finance_app/analytics.html", context)



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
def transaction_list_by_account(request):
    user = request.user
    account_id = request.GET.get('account_id')
    qs = Transaction.objects.filter(user=user).order_by('-date')
    if account_id:
        qs = qs.filter(account__id=account_id)
    accounts = Account.objects.filter(user=user)
    return render(request, 'finance_app/transaction_list.html', {
        'transactions': qs,
        'accounts': accounts,
        'selected_account': account_id,
    })




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




