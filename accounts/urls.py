from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect_view, name='dashboard'),
    path('dashboard/caregiver/', views.caregiver_dashboard_view, name='caregiver_dashboard'),
    path('dashboard/family/', views.family_dashboard_view, name='family_dashboard'),
    path("profile/", views.profile_view, name="profile"),
]