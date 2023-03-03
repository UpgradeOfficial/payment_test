from django.contrib import admin

# Register your models here.
from .models import SubscriptionPayment, RecurringSubscriptionPayment, Feature, SubscriptionPlan


models = SubscriptionPayment, RecurringSubscriptionPayment, Feature, SubscriptionPlan

for model in models:
    admin.site.register(model)
