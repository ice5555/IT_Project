# apps/finance_app/forms.py

from django import forms
from .models import Account, Budget, Transaction, Category



class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'threshold', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # 从 kwargs 中 pop 出 user 参数，防止报错
        user = kwargs.pop('user', None)
        super(BudgetForm, self).__init__(*args, **kwargs)

class TransactionForm(forms.ModelForm):
    transaction_type = forms.ChoiceField(
        choices=Transaction.TRANSACTION_TYPE_CHOICES,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Transaction
        fields = ['account', 'amount', 'category', 'date', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        transaction_type = kwargs.pop('transaction_type', 'expense')
        super(TransactionForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)  # **确保账户属于当前用户**

        self.fields['category'].queryset = Category.objects.filter(category_type=transaction_type)
        self.fields['transaction_type'].initial = transaction_type


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'account_type', 'currency']


