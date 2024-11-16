from django.contrib import admin
from .models import ExpenseRecord, DailyExpense

admin.site.register(ExpenseRecord)
admin.site.register(DailyExpense)