from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import CareCircleMember, CareProfile, Medication, MedicationLog, MedicationSchedule

User = get_user_model()


def _input(**attrs):
    return {'class': 'form-input', **attrs}


class CareProfileForm(forms.ModelForm):
    class Meta:
        model = CareProfile
        fields = [
            'full_name', 'birth_date', 'blood_type', 'conditions',
            'allergies', 'insurance_info', 'emergency_medical_notes',
        ]
        labels = {
            'full_name': 'Relative\'s Full Name',
            'birth_date': 'Date of Birth',
            'insurance_info': 'Insurance (provider and number)',
            'emergency_medical_notes': 'Emergency Medical Notes',
        }
        widgets = {
            'full_name': forms.TextInput(attrs=_input(placeholder='Maria Santos')),
            'birth_date': forms.DateInput(attrs=_input(type='date'), format='%Y-%m-%d'),
            'blood_type': forms.Select(attrs=_input()),
            'conditions': forms.Textarea(attrs=_input(rows=3, placeholder='e.g. Hypertension, Type 2 diabetes')),
            'allergies': forms.Textarea(attrs=_input(rows=2, placeholder='e.g. Penicillin')),
            'insurance_info': forms.TextInput(attrs=_input()),
            'emergency_medical_notes': forms.Textarea(attrs=_input(rows=3)),
        }

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Please enter the relative\'s full name.')
        return name

    def clean_birth_date(self):
        born = self.cleaned_data['birth_date']
        today = timezone.localdate()
        if born > today:
            raise forms.ValidationError('Date of birth cannot be in the future.')
        if born < today - timedelta(days=365 * 120):
            raise forms.ValidationError('Please enter a valid date of birth.')
        return born


class AddMemberForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=_input(placeholder='Email of the person to add'))
    )

    def __init__(self, *args, profile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.user = None

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            raise forms.ValidationError('No Alaga account uses that email. Ask them to register first.')
        already = CareCircleMember.objects.filter(
            care_profile=self.profile, user=user, status=CareCircleMember.STATUS_ACTIVE
        ).exists()
        if already:
            raise forms.ValidationError('That person is already in this care circle.')
        self.user = user
        return email


class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['medication_name', 'dosage', 'start_date', 'end_date', 'is_active']
        labels = {
            'medication_name': 'Medicine Name',
            'dosage': 'Dosage (per dose)',
            'end_date': 'End Date (leave empty if ongoing)',
            'is_active': 'Currently taking this medicine',
        }
        widgets = {
            'medication_name': forms.TextInput(attrs=_input(placeholder='Metformin')),
            'dosage': forms.TextInput(attrs=_input(placeholder='500 mg, 1 tablet')),
            'start_date': forms.DateInput(attrs=_input(type='date'), format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs=_input(type='date'), format='%Y-%m-%d'),
        }

    def __init__(self, *args, creating=False, **kwargs):
        super().__init__(*args, **kwargs)
        if creating:
            del self.fields['is_active']

    def clean_medication_name(self):
        return self.cleaned_data['medication_name'].strip()

    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        if start and end and end < start:  # BR-10
            self.add_error('end_date', 'End date cannot be earlier than the start date.')
        return data


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = MedicationSchedule
        fields = ['dose_time', 'reminder_minutes']
        labels = {
            'dose_time': 'Dose Time',
            'reminder_minutes': 'Remind (minutes before, 0 to 120)',
        }
        widgets = {
            'dose_time': forms.TimeInput(attrs=_input(type='time'), format='%H:%M'),
            'reminder_minutes': forms.NumberInput(attrs=_input(min=0, max=120, placeholder='Optional')),
        }

    def __init__(self, *args, medication=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.medication = medication

    def clean_reminder_minutes(self):
        minutes = self.cleaned_data.get('reminder_minutes')
        if minutes is not None and not 0 <= minutes <= 120:  # BR-11
            raise forms.ValidationError('Reminder must be from 0 to 120 minutes.')
        return minutes

    def clean_dose_time(self):
        dose_time = self.cleaned_data['dose_time']
        if self.medication is not None:
            taken = MedicationSchedule.objects.filter(medication=self.medication, dose_time=dose_time)
            if self.instance.pk:
                taken = taken.exclude(pk=self.instance.pk)
            if taken.exists():
                raise forms.ValidationError('This medicine already has a dose at that time.')
        return dose_time


class ReminderForm(forms.ModelForm):
    class Meta:
        model = MedicationSchedule
        fields = ['reminder_minutes']

    def clean_reminder_minutes(self):
        minutes = self.cleaned_data.get('reminder_minutes')
        if minutes is not None and not 0 <= minutes <= 120:
            raise forms.ValidationError('Reminder must be from 0 to 120 minutes.')
        return minutes


class DoseStatusForm(forms.Form):
    status = forms.ChoiceField(choices=MedicationLog.STATUS_CHOICES)


class DoseLogForm(DoseStatusForm):
    scheduled_date = forms.DateField(required=False)

    def clean_scheduled_date(self):
        date = self.cleaned_data.get('scheduled_date') or timezone.localdate()
        if date > timezone.localdate():  # BR-08
            raise forms.ValidationError('A dose cannot be logged for a future date.')
        return date