from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, LoginForm


def get_role_dashboard_url(user):
    if user.role == 'caregiver':
        return 'caregiver_dashboard'
    return 'family_dashboard'


def role_required(allowed_role):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role != allowed_role:
                messages.error(request, 'Access denied: You do not have permission to view that dashboard.')
                return redirect(get_role_dashboard_url(request.user))
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def register_view(request):
    if request.user.is_authenticated:
        return redirect(get_role_dashboard_url(request.user))

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.full_name}! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        logout(request)  # Clear the session so they can switch accounts or re-login cleanly

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                return redirect(next_url or get_role_dashboard_url(user))
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
        else:
            messages.error(request, 'Please enter a valid email and password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard_redirect_view(request):
    return redirect(get_role_dashboard_url(request.user))


@role_required('caregiver')
def caregiver_dashboard_view(request):
    return render(request, 'accounts/caregiver_dashboard.html')


@role_required('family')
def family_dashboard_view(request):
    return render(request, 'accounts/family_dashboard.html')