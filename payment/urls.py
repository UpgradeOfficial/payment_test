from django.urls import path
from .views import (
    SubscriptionView,
    FlutterwaveWebhookView,
    PaymentListAPIView,
    UpdateSubscriptionPlanView,
    ListSubscriptionPlanView,
    CreateFeatureView,
    ListFeatureView,
    RetrieveUpdateDeleteFeatureView,
    ActivateCancelSubscriptionView,
)

urlpatterns = [
    path("subscribe/", SubscriptionView.as_view(), name="subscribe"),
    path(
        "subscribe/toggle-status/",
        ActivateCancelSubscriptionView.as_view(),
        name="unsubscribe_or_resubscribe",
    ),
    path("all/", PaymentListAPIView.as_view(), name="all_payment"),
    path(
        "flutterwave-webhook/",
        FlutterwaveWebhookView.as_view(),
        name="flutterwave-webhook",
    ),
    path(
        "subscription-plan/<pk>/",
        UpdateSubscriptionPlanView.as_view(),
        name="update-subscription-plan",
    ),
    path(
        "subscription-plans/all/",
        ListSubscriptionPlanView.as_view(),
        name="list-subscription-plan",
    ),
    path(
        "features/all/",
        ListFeatureView.as_view(),
        name="list-features",
    ),
    path(
        "feature/",
        CreateFeatureView.as_view(),
        name="create-feature",
    ),
    path(
        "feature/<pk>/",
        RetrieveUpdateDeleteFeatureView.as_view(),
        name="update-delete-feature",
    ),
]
