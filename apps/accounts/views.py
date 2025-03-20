# apps/accounts/views.py
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 注册成功后自动登录
            return redirect('/accounts/login/')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})