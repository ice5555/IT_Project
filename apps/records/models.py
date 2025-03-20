from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

# 币种相关选项
CURRENCY_CHOICES = [
    ('GBP', 'British Pound (GBP)'),
    ('CNY', 'Chinese Yuan (CNY)'),
    ('TWD', 'New Taiwan Dollar (TWD)'),
    ('USD', 'US Dollar (USD)'),
    ('EUR', 'Euro (EUR)'),
    ('JPY', 'Japanese Yen (JPY)'),
    ('AUD', 'Australian Dollar (AUD)'),
    ('CAD', 'Canadian Dollar (CAD)'),
    ('HKD', 'Hong Kong Dollar (HKD)')
]


CURRENCY_SYMBOLS = {
    'GBP': '£',
    'CNY': '￥',
    'TWD': 'NT$',
    'USD': '$',
    'EUR': '€',
    'JPY': '¥',
    'AUD': 'A$',
    'CAD': 'C$',
    'HKD': 'HK$'
}

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    account_type = models.CharField(max_length=50, blank=True, null=True)  # 如“银行卡”、“现金”、“电子钱包”
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')

    def __str__(self):
        return f"{self.name} ({self.get_currency_display()}) - Balance: {self.balance}"

    def get_currency_symbol(self):
        return CURRENCY_SYMBOLS.get(self.currency, '')

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f"Budget: {self.amount} from {self.start_date.date()} to {self.end_date.date()}"

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50) 
    date = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.category}: {self.amount}"

    def get_currency_symbol(self):
        return self.account.get_currency_symbol()
