from django.db import models
import uuid
from django.utils import timezone

from core.managers import CustomManager


class CoreModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    all_objects = models.Manager()
    objects = CustomManager()

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return self.__str__()

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.is_deleted = True
        self.save()

    @classmethod
    def from_validated_data(cls, validated_data: dict, *args, **kwargs):
        fields = [field.name for field in cls._meta.fields]

        constructor_kwargs = {
            field: validated_data.pop(field)
            for field in fields
            if field in validated_data
        }
        return cls(**constructor_kwargs)

    class Meta:
        abstract = True
