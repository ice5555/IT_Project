from apps.records.serializers import ExpenseRecordSerializer
from apps.records.models import ExpenseRecord

def test_expense_record_serializer():
    record = ExpenseRecord(
        product_name="Mango",
        quantity=4,
        total_price=40,
        estimated_usage_days=4
    )
    serializer = ExpenseRecordSerializer(record)
    data = serializer.data
    assert data["product_name"] == "Mango"
    assert data["total_price"] == 40
    assert data["estimated_usage_days"] == 4
