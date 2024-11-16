import pytest
from rest_framework.test import APIClient
from apps.records.models import ExpenseRecord

@pytest.mark.django_db
def test_create_expense_record():
    client = APIClient()
    data = {
        "product_name": "Banana",
        "quantity": 6,
        "total_price": 30,
        "estimated_usage_days": 6
    }
    response = client.post("/api/expense-records/", data, format='json')
    assert response.status_code == 201
    assert response.data["product_name"] == "Banana"
    assert response.data["total_price"] == 30

@pytest.mark.django_db
def test_get_expense_records():
    client = APIClient()
    ExpenseRecord.objects.create(
        product_name="Grapes",
        quantity=3,
        total_price=15,
        estimated_usage_days=3
    )
    response = client.get("/api/expense-records/")
    assert response.status_code == 200
    assert len(response.data) > 0
