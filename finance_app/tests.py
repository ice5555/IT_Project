# tests.py
from io import StringIO
import csv
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

# 导入你应用中的模型，注意这里假设 Category 也存在
from finance_app.models import Account, Transaction, Budget, Category

class FinanceAppViewsTest(TestCase):
    def setUp(self):
        # 创建测试用户，并模拟登录
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        # 创建测试数据：账户、分类、交易和预算
        self.account = Account.objects.create(
            user=self.user, 
            name="Test Account", 
            balance=1000,
            account_type="savings",   # 确保 AccountForm 要求的字段
            currency="USD"
        )        
        self.category_income = Category.objects.create(name="Salary", category_type='income')
        self.category_expense = Category.objects.create(name="Food", category_type='expense')

        self.tx_income = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=200,
            transaction_type='income',
            date=timezone.now() - datetime.timedelta(days=1),
            category=self.category_income,
            note="Income test"
        )
        # 创建支出交易
        self.tx_expense = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=50,
            transaction_type='expense',
            date=timezone.now() - datetime.timedelta(days=2),
            category=self.category_expense,
            note="Expense test"
        )
        # 创建预算数据
        self.budget = Budget.objects.create(
            user=self.user,
            amount=500,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + datetime.timedelta(days=30)).date(),
            category=self.category_expense,
            threshold=0.8  # 假设 threshold 也是必填字段
        )

    def test_dashboard_view(self):
        """
        测试 dashboard 视图是否正确返回上下文数据。
        """
        url = reverse('finance_app:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # 检查返回的上下文是否包含预期的键
        context = response.context
        self.assertIn('accounts', context)
        self.assertIn('total_balance', context)
        self.assertEqual(context['total_balance'], self.account.balance)
        self.assertIn('recent_transactions', context)
        self.assertIn('total_income', context)
        self.assertIn('total_expense', context)
        self.assertIn('budget_remaining', context)
        self.assertIn('category_distribution', context)

    def test_dashboard_filter_ajax_this_month(self):
        """
        测试 dashboard_filter_ajax 视图：传入 range=this_month 后返回正确的数据格式
        """
        url = reverse('finance_app:dashboard_filter_ajax')
        response = self.client.get(url, {'range': 'this_month'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_income', data)
        self.assertIn('total_expense', data)
        self.assertIn('category_distribution', data)
        self.assertIn('recent_transactions', data)

    def test_transaction_create_view_get(self):
        """
        测试 transaction_create 视图的 GET 请求，确保能正确渲染表单页面
        """
        url = reverse('finance_app:transaction_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # 这里可以检查返回内容中是否包含表单相关字段
        self.assertContains(response, '<form')

    def test_analytics_view(self):
        """
        测试 analytics 视图，确保返回的上下文数据包含必要的统计信息
        """
        url = reverse('finance_app:analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn('income_trend_dates', context)
        self.assertIn('income_trend_values', context)
        self.assertIn('expense_trend_values', context)
        self.assertIn('category_distribution', context)
        self.assertIn('account_data', context)

    def test_export_transactions_csv(self):
        """
        测试 export_transactions_csv 视图，验证返回 CSV 文件格式
        """
        url = reverse('finance_app:export_transactions_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        # 解析 CSV 内容验证表头
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        header = next(reader)
        expected_header = ['ID', 'Date', 'Type', 'Category', 'Account', 'Amount', 'Note']
        self.assertEqual(header, expected_header)


    def test_account_delete(self):
        """
        测试 account_delete 视图的 POST 请求，删除账户
        """
        url = reverse('finance_app:account_delete', kwargs={'pk': self.account.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(Account.DoesNotExist):
            Account.objects.get(pk=self.account.pk)

    def test_account_list(self):
        """
        测试 account_list 视图，确保能显示账户列表
        """
        url = reverse('finance_app:account_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.account.name)

    def test_transaction_delete(self):
        """
        测试 transaction_delete 视图的 POST 请求，删除交易记录
        """
        url = reverse('finance_app:transaction_delete', kwargs={'pk': self.tx_expense.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(Transaction.DoesNotExist):
            Transaction.objects.get(pk=self.tx_expense.pk)

    def test_transaction_list(self):
        """
        测试 transaction_list 视图，确保能显示交易列表
        """
        url = reverse('finance_app:transaction_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Income test")
        self.assertContains(response, "Expense test")

    # ---------------------------
    # 预算（Budget）相关测试
    # ---------------------------
    def test_add_budget(self):
        """
        测试 add_budget 视图的 POST 请求，创建新预算
        """
        url = reverse('finance_app:add_budget')
        data = {
            'category': self.category_expense.pk,
            'amount': 600,
            'threshold': 0.8,
            'start_date': timezone.now().strftime("%Y-%m-%d"),
            'end_date': (timezone.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        budget = Budget.objects.get(amount=600, user=self.user)
        self.assertEqual(budget.category, self.category_expense)
