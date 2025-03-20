from django.apps import AppConfig

class FinanceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance_app'

    def ready(self):
        from .models import Category
        Category.initialize_categories()