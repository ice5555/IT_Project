from django.db import models
from datetime import timedelta, date
from decimal import Decimal


class ExpenseRecord(models.Model):
    description = models.CharField(max_length=200)  # 描述或商品名称
    specification = models.CharField(max_length=50, blank=True, null=True)  # 规格（如 450g, 6个）
    category = models.CharField(max_length=100)  # 支持自定义输入
    tags = models.CharField(max_length=200, blank=True, null=True)  # 标签字段（如 #水果, #零食）
    
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # 原价
    current_price = models.DecimalField(max_digits=10, decimal_places=2)  # 实际支付金额
    
    discount_type = models.CharField(max_length=100, blank=True, null=True)  # 自定义折扣类型
    store = models.CharField(max_length=100, blank=True, null=True)  # 购买地点

    estimated_usage_days = models.IntegerField()  # 预估使用天数
    actual_usage_days = models.IntegerField(blank=True, null=True, default=0)
    purchase_date = models.DateField(default=date.today)  # 支出日期
    expiration_date = models.DateField(blank=True, null=True)  # 过期日期（可选）

    notes = models.TextField(blank=True, null=True)  # 备注

    def __str__(self):
        return f"{self.description} - {self.current_price}"
    
    def save(self, *args, **kwargs):
        # 如果没有填写原价，则原价等于现价（无折扣）
        if not self.original_price:
            self.original_price = self.current_price
        super().save(*args, **kwargs)
        # 在首次创建时生成每日开销记录
        if not self.daily_expenses.exists():
            self.generate_daily_expenses()

    def generate_daily_expenses(self):
        """生成每日开销记录"""
        daily_cost = self.current_price / self.estimated_usage_days
        expenses = []
        for i in range(self.estimated_usage_days):
            expenses.append(
                DailyExpense(
                    expense_record=self,
                    date=self.purchase_date + timedelta(days=i),
                    daily_cost=daily_cost
                )
            )
        DailyExpense.objects.bulk_create(expenses)

    def update_daily_expenses(self):
        """根据实际使用天数调整每日开销"""
        if self.actual_usage_days:
            # 删除原有的每日开销记录
            self.daily_expenses.all().delete()
            
            # 根据实际使用天数重新生成每日开销
            daily_cost = self.current_price / self.actual_usage_days
            expenses = []
            for i in range(self.actual_usage_days):
                expenses.append(
                    DailyExpense(
                        expense_record=self,
                        date=self.purchase_date + timedelta(days=i),
                        daily_cost=daily_cost
                    )
                )
            DailyExpense.objects.bulk_create(expenses)


class DailyExpense(models.Model):
    expense_record = models.ForeignKey(
        'ExpenseRecord',
        on_delete=models.CASCADE,
        related_name='daily_expenses'
    )
    date = models.DateField()
    daily_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.daily_cost}"


class IncomeRecord(models.Model):
    source = models.CharField(max_length=100)  # 收入来源，例如：工资、投资、礼金等
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 收入金额
    category = models.CharField(max_length=100)  # 收入类别，支持自定义
    date = models.DateField(default=date.today)  # 收入日期，默认为当天
    tags = models.CharField(max_length=200, blank=True, null=True)
    note = models.TextField(blank=True, null=True)  # 备注

    def __str__(self):
        return f"{self.source} - £{self.amount}"
