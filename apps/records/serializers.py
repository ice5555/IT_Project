from rest_framework import serializers
from .models import ExpenseRecord, DailyExpense, IncomeRecord

class ExpenseRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseRecord
        fields = '__all__'
        read_only_fields = ('user',)


class DailyExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyExpense
        fields = '__all__'
        read_only_fields = ('user',)

class IncomeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeRecord
        fields = '__all__'
        read_only_fields = ('user',)
