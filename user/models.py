from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import CoreModel
from django.utils.translation import gettext_lazy as _


# Create your models here.


class User(AbstractUser, CoreModel):
    email = models.EmailField(_("email"), unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return self.email

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"
