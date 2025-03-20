# apps/records/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, Value, DecimalField, F
from django.db.models.functions import Upper, Trim
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from datetime import datetime

from .models import Transaction, CURRENCY_SYMBOLS
from .serializers import TransactionSerializer
from .forms import TransactionForm

import logging
import csv

logger = logging.getLogger(__name__)

class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = Transaction.objects.values_list('category', flat=True).disctinct()
        return Response(list(categories), status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        today=timezone.now()
        start_of_month=today.replace(day=1)
        transactions = Transaction.objects.filter(date__gte=start_of_month)

        total_income = transactions.filter(transaction_type="income").aggregate(total=Sum('amount'))['total'] or 0
        total_expense = transactions.filter(transaction_type="expense").aggregate(total=Sum('amount'))['total'] or 0
        category_expenses = transactions.filter(transaction_type="expense").values('category').annotate(total=Sum('amount'))
        
        return Response({
            "total_income": total_income,
            "total_expense": total_expense,
            "category_expenses": list(category_expenses)
        })

@login_required
def transaction_list(request):
    """Display all transactions"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'records/transaction_list.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    """Add new transaction"""
    if request.method == 'POST':
        category = request.POST.get('category')
        amount = request.POST.get('amount')
        transaction_type = request.POST.get('transaction_type')
        Transaction.objects.create(user=request.user, category=category, amount=amount, transaction_type=transaction_type)
        return redirect('transaction_list')

    return render(request, 'records/add_transaction.html')

@login_required
def edit_transaction(request, pk):
    """Edit transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        transaction.category = request.POST.get('category')
        transaction.amount = request.POST.get('amount')
        transaction.transaction_type = request.POST.get('transaction_type')
        transaction.save()
        return redirect('transaction_list')

    return render(request, 'records/edit_transaction.html', {'transaction': transaction})

@login_required
def delete_transaction(request, pk):
    """Delete transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transaction_list')

    return render(request, 'records/delete_transaction.html', {'transaction': transaction})

@login_required
def export_transactions(request):
    """Export transactions as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Amount', 'Type', 'Date'])

    transactions = Transaction.objects.filter(user=request.user)
    for transaction in transactions:
        writer.writerow([transaction.category, transaction.amount, transaction.transaction_type, transaction.date])

    return response

@login_required
def import_transactions(request):
    """Import transactions from CSV"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        next(reader)  # Skip header row

        for row in reader:
            Transaction.objects.create(
                user=request.user,
                category=row[0],
                amount=row[1],
                transaction_type=row[2],
                date=row[3]
            )
        return redirect('transaction_list')

    return render(request, 'records/import_transactions.html')

# 自动补全接口
@login_required
def store_autocomplete(request):
    query = request.GET.get('q', '')
    stores = ExpenseRecord.objects.filter(store__icontains=query).values_list('store', flat=True).distinct()
    return JsonResponse(list(stores), safe=False)


