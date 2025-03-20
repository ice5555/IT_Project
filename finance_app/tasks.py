from celery import shared_task
from django.utils import timezone
from .models import Budget

@shared_task
def check_all_users_budget():
    """检查所有用户的预算，并发送提醒"""
    today = timezone.now()
    for budget in Budget.objects.all():
        budget.check_budget_exceeded()  # 调用 Budget 模型的方法，检查是否超出预算
