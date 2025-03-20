from django.test import TestCase

# Create your tests here.
# finance_app/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Account, Transaction

class FinanceAppTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123')
        self.account = Account.objects.create(user=self.user, name='Test Account', balance=1000)

    def test_create_transaction(self):
        self.client.login(username='testuser', password='TestPass123')
        response = self.client.post('/transactions/create/', {
            'account': self.account.id,
            'amount': 200,
            'category': 'Food',
            'transaction_type': 'expense',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)
        tx = Transaction.objects.first()
        self.assertEqual(tx.category, 'Food')
        self.assertEqual(tx.amount, 200)
