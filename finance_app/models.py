# apps/finance_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.core.mail import send_mail

CURRENCY_CHOICES = [
    ('GBP', '£'),
    ('USD', '$'),
    ('EUR', '€'),
    ('CNY', '¥'),
    ('TWD', 'NT$'),
]

ACCOUNT_TYPE_CHOICES = [
    ('cash', 'Cash'),
    ('bank', 'Bank'),
    ('credit_card', 'Credit Card'),
    ('paypal', 'PayPal'),
    ('apple_pay', 'Apple Pay'),
    ('google_pay', 'Google Pay'),
    ('other', 'Other'),
]

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # 账户名称，如“招商银行储蓄卡”
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='bank')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()}) - {self.currency}{self.balance}"

    def get_currency_symbol(self):
        return dict(CURRENCY_CHOICES).get(self.currency, '')




class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense')
    ]

    DEFAULT_CATEGORIES = [
        # Expense Categories
        ('Healthcare', 'expense'),
        ('Transport', 'expense'),
        ('Food', 'expense'),
        ('Sports', 'expense'),
        ('Gaming', 'expense'),
        ('Travel', 'expense'),
        ('Daily', 'expense'),
        ('Haircut', 'expense'),
        ('Shopping', 'expense'),

        # Income Categories
        ('Salary', 'income', ),
        ('Stocks', 'income'),
        ('Gifts', 'income'),
        ('Red Packet', 'income'),
        ('Investment', 'income'),
        ('Allowance', 'income'),
        ]

    name = models.CharField(max_length=50, unique=True)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)  # 区分收入/支出类别
    icon = models.CharField(max_length=255, default="icons/default.svg")  # 这里确保路径正确
    
    def get_icon_url(self):
        return f"icons/{self.name.lower()}.svg"  # 让前端直接拼接路径


    def __str__(self):
        return self.name

    @classmethod
    def initialize_categories(cls):
        """ 确保默认类别存在 """
        for name, category_type in cls.DEFAULT_CATEGORIES:
            cls.objects.get_or_create(name=name, category_type=category_type)

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)  # 使用外键
    date = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.category}: {self.amount}"


    def save(self, *args, **kwargs):
        # 判断是新建还是更新
        is_new = self.pk is None
        if is_new:
            super().save(*args, **kwargs)
            self._update_account_balance_on_create()
        else:
            old_instance = Transaction.objects.get(pk=self.pk)
            super().save(*args, **kwargs)
            self._update_account_balance_on_update(old_instance)

        if self.transaction_type == 'expense' and self.category:
            budgets = Budget.objects.filter(user=self.user, category=self.category)
            for budget in budgets:
                budget.check_budget_exceeded()


    def delete(self, *args, **kwargs):
        self._update_account_balance_on_delete()
        super().delete(*args, **kwargs)

    def _update_account_balance_on_create(self):
        """新建交易时，根据交易类型更新对应账户余额"""
        if self.transaction_type == 'income':
            self.account.balance += self.amount
        else:
            self.account.balance -= self.amount
        self.account.save()

    def _update_account_balance_on_update(self, old_instance):
        """更新交易时，需考虑金额、类型、账户是否有变化"""
        # 1. 如果账户没变，只是金额或类型变了，需要先把旧的影响去掉，再加上新的
        if old_instance.account == self.account:
            # 先把旧记录的影响移除
            if old_instance.transaction_type == 'income':
                self.account.balance -= old_instance.amount
            else:
                self.account.balance += old_instance.amount

            # 再加上新记录的影响
            if self.transaction_type == 'income':
                self.account.balance += self.amount
            else:
                self.account.balance -= self.amount
            self.account.save()
        else:
            # 如果用户换了账户，需要更新旧账户和新账户的余额
            old_account = old_instance.account
            if old_instance.transaction_type == 'income':
                old_account.balance -= old_instance.amount
            else:
                old_account.balance += old_instance.amount
            old_account.save()

            if self.transaction_type == 'income':
                self.account.balance += self.amount
            else:
                self.account.balance -= self.amount
            self.account.save()

    def _update_account_balance_on_delete(self):
        """删除交易时，恢复对应账户的余额"""
        if self.transaction_type == 'income':
            self.account.balance -= self.amount
        else:
            self.account.balance += self.amount
        self.account.save()


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)  # 预算针对具体类别
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 预算金额
    threshold = models.DecimalField(max_digits=5, decimal_places=2, default=80)  # ✅ 预算阈值（默认80%）
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    last_notified = models.DateTimeField(null=True, blank=True)  # ✅ 记录上次通知时间，避免重复通知

    def __str__(self):
        return f"{self.user.username} - {self.category.name}: £{self.amount}"

    def get_spent_percentage(self):
        """ 计算当前支出的百分比 """
        total_spent = sum(tx.amount for tx in self.user.transaction_set.filter(
            category=self.category,
            transaction_type='expense',
            date__range=(self.start_date, self.end_date)
        ))
        return (total_spent / self.amount) * 100 if self.amount else 0

    def check_budget_exceeded(self):
        """ 检查预算是否超额，并在超额时发送提醒 """
        spent_percentage = self.get_spent_percentage()
        if spent_percentage >= self.threshold:  # ✅ 预算达到阈值
            if not self.last_notified or (timezone.now() - self.last_notified).days >= 1:
                self.send_budget_alert(spent_percentage)
                self.last_notified = timezone.now()
                self.save()

    def send_budget_alert(self, spent_percentage):
        """ 发送超预算提醒邮件 """
        total_expense = Transaction.objects.filter(
        user=self.user, 
        category=self.category, 
        transaction_type="expense"
    ).aggregate(total=models.Sum('amount'))['total'] or 0  # 避免 None

        subject = f"🚨 Budget Alert: {self.category}"
        message = f"Your spending on {self.category} has reached {spent_percentage:.2f}% of your budget.\n\n"\
                    f"Total spent: £{total_expense}\n\n"
        send_mail(subject, message, "noreply@yourapp.com", [self.user.email])

   




