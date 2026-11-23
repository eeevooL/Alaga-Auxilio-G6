from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from care.models import MedicationLog, MedicationSchedule


class Command(BaseCommand):
    help = 'BR-09: mark today\'s doses as Missed if they were not logged within 2 hours of the dose time.'

    def handle(self, *args, **options):
        now = timezone.localtime()
        today = now.date()
        schedules = (
            MedicationSchedule.objects
            .filter(
                medication__is_active=True,
                medication__care_profile__is_active=True,
                medication__start_date__lte=today,
            )
            .filter(Q(medication__end_date__isnull=True) | Q(medication__end_date__gte=today))
            .exclude(logs__scheduled_date=today)
        )
        created = 0
        for schedule in schedules:
            due = timezone.make_aware(datetime.combine(today, schedule.dose_time))
            if now >= due + timedelta(hours=2):
                MedicationLog.objects.get_or_create(
                    schedule=schedule, scheduled_date=today,
                    defaults={'status': MedicationLog.STATUS_MISSED, 'logged_by': None},
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Marked {created} dose(s) as Missed.'))