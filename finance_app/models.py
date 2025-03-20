# apps/finance_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

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



class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()

    def __str__(self):
        return f"Budget: {self.amount} from {self.start_date.date()} to {self.end_date.date()}"


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


