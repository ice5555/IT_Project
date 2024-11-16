import pytest
from apps.records.models import ExpenseRecord, DailyExpense

@pytest.mark.django_db
def test_expense_record_creation():
    record = ExpenseRecord.objects.create(
        product_name="Apple",
        quantity=5,
        total_price=50,
        estimated_usage_days=5
    )
    assert record.product_name == "Apple"
    assert record.total_price == 50
    assert record.estimated_usage_days == 5

@pytest.mark.django_db
def test_daily_expenses_creation():
    record = ExpenseRecord.objects.create(
        product_name="Orange",
        quantity=10,
        total_price=100,
        estimated_usage_days=10
    )
    record.generate_daily_expenses()
    expenses = DailyExpense.objects.filter(expense_record=record)
    assert len(expenses) == 10
    assert expenses[0].daily_cost == 10
