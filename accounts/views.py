from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, LoginForm, UserProfileForm
from care.models import CareProfile


ROLE_FAMILY = 'Remote Family'
ROLE_CAREGIVER = 'Local Caregiver'

ROLE_DASHBOARDS = {
    ROLE_FAMILY: 'family_dashboard',
    ROLE_CAREGIVER: 'caregiver_dashboard',
}


def get_role_dashboard_url(user):
    # If role unknown -> login
    return ROLE_DASHBOARDS.get(user.role, 'login')


def role_required(allowed_role):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
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


def _circle_profiles(user):
    return CareProfile.objects.filter(
        is_active=True, members__user=user, members__status='Active'
    )


@role_required(ROLE_CAREGIVER)
def caregiver_dashboard_view(request):
    return render(request, 'accounts/caregiver_dashboard.html', {
        'care_profiles': _circle_profiles(request.user),
    })


@role_required(ROLE_FAMILY)
def family_dashboard_view(request):
    return render(request, 'accounts/family_dashboard.html', {
        'care_profiles': _circle_profiles(request.user),
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile details have been updated.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(
        request,
        'accounts/profile.html',
        {
            'form': form,
            'user_obj': request.user,
            'dashboard_url_name': get_role_dashboard_url(request.user),
        },
    )