from django.contrib import admin

from .models import CareCircleMember, CareProfile, Medication, MedicationLog, MedicationSchedule

admin.site.register(CareProfile)
admin.site.register(CareCircleMember)
admin.site.register(Medication)
admin.site.register(MedicationSchedule)
admin.site.register(MedicationLog)