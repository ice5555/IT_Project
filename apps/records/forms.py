from django import forms
from .models import ExpenseRecord, IncomeRecord

class ExpenseRecordForm(forms.ModelForm):
    class Meta:
        model = ExpenseRecord
        fields = ['description', 'specification', 'category', 'tags', 'original_price', 'current_price', 'discount_type', 'store', 'estimated_usage_days', 'purchase_date', 'expiration_date', 'notes']

class IncomeRecordForm(forms.ModelForm):
    class Meta:
        model = IncomeRecord
        fields = ['source', 'amount', 'category', 'date', 'tags', 'note']