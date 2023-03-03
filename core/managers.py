from django.db import models
from django.utils import timezone


class CustomManager(models.Manager):
    def get_queryset(
        self,
    ):
        return super().get_queryset().filter(is_deleted=False)

    def include_all(
        self,
    ):
        return super().get_queryset()

    def delete(self):
        return super().get_queryset().update(is_deleted=True, deleted_at=timezone.now())
