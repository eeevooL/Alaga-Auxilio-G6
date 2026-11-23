from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class CareProfile(models.Model):
    """Shared profile of the elderly relative, including medical info."""

    BLOOD_TYPE_CHOICES = [(b, b) for b in ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown')]

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_care_profiles'
    )
    full_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='Unknown')
    conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    insurance_info = models.CharField(max_length=150, blank=True)
    emergency_medical_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'care_profiles'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        today = timezone.localdate()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years


class CareCircleMember(models.Model):
    """Links user accounts to a shared care profile (BR-05)."""

    STATUS_ACTIVE = 'Active'
    STATUS_REMOVED = 'Removed'
    STATUS_CHOICES = [(STATUS_ACTIVE, 'Active'), (STATUS_REMOVED, 'Removed')]

    care_profile = models.ForeignKey(CareProfile, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='care_memberships'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        db_table = 'care_circle_members'
        constraints = [
            models.UniqueConstraint(fields=['care_profile', 'user'], name='unique_member_per_profile'),
        ]

    def __str__(self):
        return f'{self.user} in {self.care_profile} ({self.status})'


class Medication(models.Model):
    """A medicine of the relative."""

    care_profile = models.ForeignKey(CareProfile, on_delete=models.CASCADE, related_name='medications')
    medication_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'medications'
        ordering = ['-is_active', 'medication_name']
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F('start_date')),
                name='medication_end_date_after_start',  # BR-10
            ),
        ]

    def __str__(self):
        return f'{self.medication_name} {self.dosage}'

    def has_logs(self):
        return MedicationLog.objects.filter(schedule__medication=self).exists()


class MedicationSchedule(models.Model):
    """Daily dose time and reminder setting."""

    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='schedules')
    dose_time = models.TimeField()
    reminder_minutes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(120)],  # BR-11
    )

    class Meta:
        db_table = 'medication_schedules'
        ordering = ['dose_time']
        constraints = [
            models.UniqueConstraint(fields=['medication', 'dose_time'], name='unique_dose_time_per_medication'),
            models.CheckConstraint(
                condition=Q(reminder_minutes__isnull=True) | Q(reminder_minutes__lte=120),
                name='reminder_minutes_max_120',
            ),
        ]

    def __str__(self):
        return f'{self.medication} at {self.dose_time:%H:%M}'


class MedicationLog(models.Model):
    """Whether a scheduled dose was given or missed (BR-06 to BR-08)."""

    STATUS_GIVEN = 'Given'
    STATUS_MISSED = 'Missed'
    STATUS_CHOICES = [(STATUS_GIVEN, 'Given'), (STATUS_MISSED, 'Missed')]

    schedule = models.ForeignKey(MedicationSchedule, on_delete=models.PROTECT, related_name='logs')
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='dose_logs'
    )  # empty if the system marked it missed (BR-09)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medication_logs'
        ordering = ['-scheduled_date', '-schedule__dose_time']
        constraints = [
            models.UniqueConstraint(fields=['schedule', 'scheduled_date'], name='one_log_per_dose_per_date'),  # BR-07
            models.CheckConstraint(condition=Q(status__in=['Given', 'Missed']), name='log_status_given_or_missed'),
        ]

    def __str__(self):
        return f'{self.schedule} on {self.scheduled_date}: {self.status}'