from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

class UserRegistrationTestCase(TestCase):
    
    def test_register_user(self):
        response = self.client.post(reverse('user_auth:register'), {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)  # 注册成功应重定向
        self.assertTrue(User.objects.filter(username='testuser').exists())  # 确保用户已创建

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('user_auth:register'), {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'WrongPass123!'
        })
        self.assertEqual(response.status_code, 200)  # 注册失败应返回注册页面
        self.assertContains(response, "The two password fields didn’t match.")  # 检查错误信息

class UserLoginTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')

    def test_login_valid_user(self):
        response = self.client.post(reverse('user_auth:login'), {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)  # 登录成功应重定向
        self.assertTrue(response.wsgi_request.user.is_authenticated)  # 确保用户已登录

    def test_login_invalid_user(self):
        response = self.client.post(reverse('user_auth:login'), {
            'username': 'wronguser',
            'password': 'WrongPass123!'
        })
        self.assertEqual(response.status_code, 200)  # 登录失败应返回登录页面
        self.assertContains(response, "Please enter a correct username and password.")  # 检查错误信息

class UserLogoutTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')

    def test_logout_user(self):
        response = self.client.get(reverse('user_auth:logout'))
        self.assertEqual(response.status_code, 302)  # 注销成功应重定向
        self.assertFalse(response.wsgi_request.user.is_authenticated)  # 确保用户已注销
