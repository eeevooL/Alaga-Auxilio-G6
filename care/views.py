from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.views import ROLE_CAREGIVER, ROLE_FAMILY, role_required

from .forms import (
    AddMemberForm, CareProfileForm, DoseLogForm, DoseStatusForm,
    MedicationForm, ReminderForm, ScheduleForm,
)
from .models import CareCircleMember, CareProfile, Medication, MedicationLog, MedicationSchedule

ACTIVE = CareCircleMember.STATUS_ACTIVE


# Access helpers (only active members can view a profile)

def member_profile(user, pk):
    return get_object_or_404(
        CareProfile, pk=pk, is_active=True,
        members__user=user, members__status=ACTIVE,
    )


def owned_profile(user, pk):
    return get_object_or_404(CareProfile, pk=pk, is_active=True, created_by=user)


def member_medication(user, pk):
    return get_object_or_404(
        Medication.objects.select_related('care_profile'),
        pk=pk, care_profile__is_active=True,
        care_profile__members__user=user, care_profile__members__status=ACTIVE,
    )


def member_schedule(user, pk):
    return get_object_or_404(
        MedicationSchedule.objects.select_related('medication__care_profile'),
        pk=pk, medication__care_profile__is_active=True,
        medication__care_profile__members__user=user,
        medication__care_profile__members__status=ACTIVE,
    )


def _first_error(form):
    for errors in form.errors.values():
        return errors[0]
    return 'Please check the form and try again.'


# Care profile and care circle

@login_required
def care_profile_list(request):
    profiles = CareProfile.objects.filter(
        is_active=True, members__user=request.user, members__status=ACTIVE
    ).select_related('created_by')
    return render(request, 'care/care_profile_list.html', {'profiles': profiles})


@role_required(ROLE_FAMILY)
def care_profile_create(request):
    if request.method == 'POST':
        form = CareProfileForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                profile = form.save(commit=False)
                profile.created_by = request.user
                profile.save()
                CareCircleMember.objects.create(care_profile=profile, user=request.user)
            messages.success(request, f'Care profile for {profile.full_name} created.')
            return redirect('care_profile_detail', pk=profile.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CareProfileForm()
    return render(request, 'care/care_profile_form.html', {'form': form, 'title': 'Create Care Profile'})


def _render_profile_detail(request, profile, add_form=None):
    members = profile.members.filter(status=ACTIVE).select_related('user').order_by('user__full_name')
    is_creator = profile.created_by_id == request.user.pk
    if is_creator and add_form is None:
        add_form = AddMemberForm(profile=profile)
    return render(request, 'care/care_profile_detail.html', {
        'profile': profile, 'members': members, 'is_creator': is_creator, 'add_form': add_form,
    })


@login_required
def care_profile_detail(request, pk):
    return _render_profile_detail(request, member_profile(request.user, pk))


@role_required(ROLE_FAMILY)
def care_profile_update(request, pk):
    profile = owned_profile(request.user, pk)
    if request.method == 'POST':
        form = CareProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Care profile updated.')
            return redirect('care_profile_detail', pk=profile.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CareProfileForm(instance=profile)
    return render(request, 'care/care_profile_form.html', {'form': form, 'title': 'Edit Care Profile'})


@require_POST
@role_required(ROLE_FAMILY)
def care_member_add(request, pk):
    profile = owned_profile(request.user, pk)
    form = AddMemberForm(request.POST, profile=profile)
    if form.is_valid():
        CareCircleMember.objects.update_or_create(
            care_profile=profile, user=form.user, defaults={'status': ACTIVE}
        )
        messages.success(request, f'{form.user.full_name} was added to the care circle.')
        return redirect('care_profile_detail', pk=profile.pk)
    return _render_profile_detail(request, profile, add_form=form)


@require_POST
@role_required(ROLE_FAMILY)
def care_member_remove(request, pk, membership_id):
    profile = owned_profile(request.user, pk)
    membership = get_object_or_404(CareCircleMember, pk=membership_id, care_profile=profile, status=ACTIVE)
    if membership.user_id == profile.created_by_id:
        messages.error(request, 'The person who created the profile cannot be removed.')
    else:
        membership.status = CareCircleMember.STATUS_REMOVED
        membership.save(update_fields=['status'])
        messages.success(request, f'{membership.user.full_name} was removed from the care circle.')
    return redirect('care_profile_detail', pk=profile.pk)


# Medications (family manages, circle views)

@login_required
def medication_list(request, pk):
    profile = member_profile(request.user, pk)
    medications = profile.medications.prefetch_related('schedules')
    return render(request, 'care/medication_list.html', {
        'profile': profile, 'medications': medications,
        'can_manage': True,
    })


@login_required
def medication_create(request, pk):
    profile = member_profile(request.user, pk)
    if request.method == 'POST':
        form = MedicationForm(request.POST, creating=True)
        if form.is_valid():
            medication = form.save(commit=False)
            medication.care_profile = profile
            medication.save()
            messages.success(request, f'{medication.medication_name} added. Now add its dose times.')
            return redirect('medication_detail', pk=medication.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicationForm(creating=True, initial={'start_date': timezone.localdate()})
    return render(request, 'care/medication_form.html', {
        'form': form, 'profile': profile, 'title': 'Add Medication',
    })


def _render_medication_detail(request, medication, schedule_form=None):
    can_manage = True
    if can_manage and schedule_form is None:
        schedule_form = ScheduleForm(medication=medication)
    logs = MedicationLog.objects.filter(schedule__medication=medication).select_related(
        'schedule', 'logged_by'
    )[:30]
    return render(request, 'care/medication_detail.html', {
        'medication': medication, 'profile': medication.care_profile,
        'schedules': medication.schedules.all(), 'logs': logs,
        'can_manage': can_manage, 'schedule_form': schedule_form,
    })


@login_required
def medication_detail(request, pk):
    return _render_medication_detail(request, member_medication(request.user, pk))


@role_required(ROLE_FAMILY)
def medication_update(request, pk):
    medication = member_medication(request.user, pk)
    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medication updated.')
            return redirect('medication_detail', pk=medication.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicationForm(instance=medication)
    return render(request, 'care/medication_form.html', {
        'form': form, 'profile': medication.care_profile, 'title': 'Edit Medication',
    })


@require_POST
@role_required(ROLE_FAMILY)
def medication_delete(request, pk):
    medication = member_medication(request.user, pk)
    profile_pk = medication.care_profile_id
    if medication.has_logs():  # Mark inactive instead of deleting if logs exist
        medication.is_active = False
        medication.save(update_fields=['is_active'])
        messages.success(request, f'{medication.medication_name} already has dose logs, so it was set to inactive instead of deleted.')
        return redirect('medication_detail', pk=medication.pk)
    name = medication.medication_name
    medication.delete()
    messages.success(request, f'{name} was deleted.')
    return redirect('medication_list', pk=profile_pk)


@require_POST
@login_required
def schedule_add(request, pk):
    medication = member_medication(request.user, pk)
    form = ScheduleForm(request.POST, medication=medication)
    if form.is_valid():
        schedule = form.save(commit=False)
        schedule.medication = medication
        schedule.save()
        messages.success(request, 'Dose time added.')
        return redirect('medication_detail', pk=medication.pk)
    return _render_medication_detail(request, medication, schedule_form=form)


@require_POST
@login_required
def schedule_update(request, pk):
    schedule = member_schedule(request.user, pk)
    form = ReminderForm(request.POST, instance=schedule)
    if form.is_valid():
        form.save()
        messages.success(request, 'Reminder updated.')
    else:
        messages.error(request, _first_error(form))
    return redirect('medication_detail', pk=schedule.medication_id)


@require_POST
@role_required(ROLE_FAMILY)
def schedule_delete(request, pk):
    schedule = member_schedule(request.user, pk)
    medication_pk = schedule.medication_id
    if schedule.logs.exists():
        messages.error(request, 'This dose time already has logs. Set the medication to inactive instead.')
    else:
        schedule.delete()
        messages.success(request, 'Dose time removed.')
    return redirect('medication_detail', pk=medication_pk)


# Dose logging (caregivers log, family views)

@login_required
def dose_today(request, pk):
    profile = member_profile(request.user, pk)
    today = timezone.localdate()
    schedules = (
        MedicationSchedule.objects
        .filter(
            medication__care_profile=profile,
            medication__is_active=True,
            medication__start_date__lte=today,
        )
        .filter(Q(medication__end_date__isnull=True) | Q(medication__end_date__gte=today))
        .select_related('medication')
        .order_by('dose_time')
    )
    todays_logs = {
        log.schedule_id: log
        for log in MedicationLog.objects.filter(schedule__in=schedules, scheduled_date=today)
    }
    rows = [{'schedule': s, 'log': todays_logs.get(s.pk)} for s in schedules]
    history = MedicationLog.objects.filter(
        schedule__medication__care_profile=profile
    ).select_related('schedule__medication', 'logged_by')[:30]
    return render(request, 'care/dose_today.html', {
        'profile': profile, 'rows': rows, 'history': history, 'today': today,
        'is_caregiver': request.user.role == ROLE_CAREGIVER,
        'missed_today': sum(1 for r in rows if r['log'] and r['log'].status == MedicationLog.STATUS_MISSED),
    })


@require_POST
@role_required(ROLE_CAREGIVER)
def dose_log_create(request, schedule_id):
    schedule = member_schedule(request.user, schedule_id)
    medication = schedule.medication
    profile_pk = medication.care_profile_id
    form = DoseLogForm(request.POST)
    if not form.is_valid():
        messages.error(request, _first_error(form))
        return redirect('dose_today', pk=profile_pk)

    date = form.cleaned_data['scheduled_date']
    if not medication.is_active:
        messages.error(request, 'This medication is inactive.')
    elif date < medication.start_date or (medication.end_date and date > medication.end_date):
        messages.error(request, 'That date is outside this medication\'s start and end dates.')
    else:
        try:
            with transaction.atomic():
                MedicationLog.objects.create(
                    schedule=schedule, logged_by=request.user,
                    scheduled_date=date, status=form.cleaned_data['status'],
                )
            messages.success(request, f'{medication.medication_name} marked as {form.cleaned_data["status"]}.')
        except IntegrityError:  # Prevent duplicate logs for the same date
            messages.error(request, 'This dose already has a log for that date.')
    return redirect('dose_today', pk=profile_pk)


@require_POST
@role_required(ROLE_CAREGIVER)
def dose_log_update(request, pk):
    log = get_object_or_404(
        MedicationLog.objects.select_related('schedule__medication'),
        pk=pk,
        schedule__medication__care_profile__is_active=True,
        schedule__medication__care_profile__members__user=request.user,
        schedule__medication__care_profile__members__status=ACTIVE,
    )
    profile_pk = log.schedule.medication.care_profile_id
    form = DoseStatusForm(request.POST)
    if log.scheduled_date != timezone.localdate():
        messages.error(request, 'Only today\'s logs can be changed.')
    elif form.is_valid():
        log.status = form.cleaned_data['status']
        log.logged_by = request.user
        log.save(update_fields=['status', 'logged_by'])
        messages.success(request, f'Log changed to {log.status}.')
    else:
        messages.error(request, _first_error(form))
    return redirect('dose_today', pk=profile_pk)