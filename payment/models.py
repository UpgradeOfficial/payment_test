from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CoreModel
from user.models import User

# Create your models here.


class PaymantProvider(models.TextChoices):
    FLUTTERWAVE = "F", _("flutterwave")


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("pending")
    ACTIVE = "ACTIVE", _("active")
    FAILED = "FAILED", _("failed")
    PAUSED = "PAUSED", _("paused")


class SubscriptionPlan(CoreModel):
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    plan_id = models.CharField(max_length=40)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.active})"


class Feature(CoreModel):
    name = models.CharField(max_length=50)
    bronze = models.BooleanField(default=False)
    silver = models.BooleanField(default=False)
    gold = models.BooleanField(default=False)
    platinum = models.BooleanField(default=False)
    pay_as_you_go = models.BooleanField(default=False)


class SubscriptionPayment(CoreModel):
    payment_ref = models.CharField(max_length=50)
    base_payment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="successor",
    )
    payment_start = models.DateTimeField(null=True)
    payment_end = models.DateTimeField(null=True)
    extra_gateway_values = models.TextField(max_length=100, default="{}")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    renewal_enabled = models.BooleanField(default=True)
    amount = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    paid = models.BooleanField(
        default=False
    )  # Stores the status of the subscription payment process
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, null=True, blank=True
    )
    subscription_start = models.DateTimeField(null=True)
    subscription_end = models.DateTimeField(null=True)
    renewed = models.BooleanField(default=False)


    def add_new_payment(self, ref, start, end):
        subscription_payment = RecurringSubscriptionPayment.objects.filter(subscription=self, payment_ref=ref).first()
        if subscription_payment:
            subscription_payment.start = start
            subscription_payment.end = end
            subscription_payment.save()
        else:
            RecurringSubscriptionPayment.objects.create(subscription=self, payment_ref=ref, start=start, end=end)

    def __str__(self) -> str:
        return  f"ref:({self.payment_ref}) paid:({self.paid}) ref:({self.status})"

class RecurringSubscriptionPayment(models.Model):
    subscription = models.ForeignKey(SubscriptionPayment, on_delete=models.CASCADE, related_name="recurring_subscriptions")
    payment_ref = models.CharField(max_length=60) # TODO: Later
    start = models.DateField()
    end = models.DateField()


    class Meta:
        ordering = ('-start',)