from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from shop.models import Order

def login_view(request):
    # If already logged in redirect appropriately
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/admin/')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Staff / Superusers go straight to admin panel
                if user.is_staff or user.is_superuser:
                    messages.success(request, f"Welcome, {username}! Redirecting to admin…")
                    next_url = request.GET.get('next', '/admin/')
                    return redirect(next_url)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('accounts:dashboard')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Amina's Vails.")
            return redirect('accounts:dashboard')
        for error in form.errors.values():
            messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')

@login_required
def dashboard_view(request):
    # Retrieve orders associated with user's email
    user_orders = Order.objects.filter(email=request.user.email)
    return render(request, 'accounts/dashboard.html', {
        'orders': user_orders
    })
