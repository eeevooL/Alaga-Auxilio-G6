from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, role, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        if not full_name:
            raise ValueError('Full name is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)
        user.set_password(password)  # BR-03: hashes password securely
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, role='Remote Family', password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('Remote Family', 'Remote Family Member'),
        ('Local Caregiver', 'Local Caregiver'),
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)  # BR-01
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)  # BR-02
    push_endpoint = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.role})"