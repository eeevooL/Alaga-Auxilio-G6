from django.urls import path

from . import views

urlpatterns = [
    # Care profile and care circle
    path('profiles/', views.care_profile_list, name='care_profile_list'),
    path('profiles/new/', views.care_profile_create, name='care_profile_create'),
    path('profiles/<int:pk>/', views.care_profile_detail, name='care_profile_detail'),
    path('profiles/<int:pk>/edit/', views.care_profile_update, name='care_profile_update'),
    path('profiles/<int:pk>/members/add/', views.care_member_add, name='care_member_add'),
    path('profiles/<int:pk>/members/<int:membership_id>/remove/', views.care_member_remove, name='care_member_remove'),

    # Medications
    path('profiles/<int:pk>/medications/', views.medication_list, name='medication_list'),
    path('profiles/<int:pk>/medications/new/', views.medication_create, name='medication_create'),
    path('medications/<int:pk>/', views.medication_detail, name='medication_detail'),
    path('medications/<int:pk>/edit/', views.medication_update, name='medication_update'),
    path('medications/<int:pk>/delete/', views.medication_delete, name='medication_delete'),
    path('medications/<int:pk>/schedules/add/', views.schedule_add, name='schedule_add'),
    path('schedules/<int:pk>/reminder/', views.schedule_update, name='schedule_update'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    # Dose logging
    path('profiles/<int:pk>/today/', views.dose_today, name='dose_today'),
    path('schedules/<int:schedule_id>/log/', views.dose_log_create, name='dose_log_create'),
    path('logs/<int:pk>/update/', views.dose_log_update, name='dose_log_update'),
]