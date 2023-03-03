import json
from rest_framework.views import APIView
from .serializers import (
    SubscriptionChargeSerializer,
    SubscriptionPaymentSerializer,
    SubscriptionPlanSerializer,
    FeatureSerializer,
    ActivateCancelSubscriptionViewSerializer,
)
from .models import SubscriptionPayment, SubscriptionPlan, Feature, PaymentStatus

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from .flutterwave import FlutterwaveProvider
from rest_framework.response import Response
from rest_framework import status, generics

from rest_framework.exceptions import ValidationError


class SubscriptionView(CreateAPIView):
    serializer_class = SubscriptionChargeSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        plan_id = data["plan_id"]
        email = data["email"]
        plan = SubscriptionPlan.objects.filter(plan_id=plan_id, active=True)
        if not plan.exists():
            raise ValidationError("Plan ID does not exist")
        plan = plan.first()
        id, auth_url = FlutterwaveProvider().subscribe(email=email, plan=plan)
        serializer.context["approval_url"] = auth_url


class ActivateCancelSubscriptionView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ActivateCancelSubscriptionViewSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription_status = serializer.validated_data["status"]
        subscription_id = serializer.validated_data["subscription"]
        subscriptions_filter = SubscriptionPayment.objects.filter(
            id=subscription_id, user=self.request.user, paid=True
        )
        if not subscriptions_filter.exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": "Either subscription does not exist \
                    or you are not the owner of the subscription or hasn't been paid."
                },
            )
        subscription = subscriptions_filter.first()
        # if not subscription.paid or subscription.extra_gateway_values == "":
        #     return Response(
        #         status=status.HTTP_400_BAD_REQUEST,
        #         data={
        #             "message": "Subscription is not paid\
        #                   or extra gateway values sub id not present"
        #         },
        #     )
        subscription_extra_kwargs_data = json.loads(subscription.extra_gateway_values)
        sub_id = subscription_extra_kwargs_data["sub_id"]
        data = {}
        if subscription_status and subscription.status == PaymentStatus.PAUSED:
            data = FlutterwaveProvider().activate_subscription(sub_id)
            subscription.status = PaymentStatus.ACTIVE
        elif (
            subscription_status is False and subscription.status == PaymentStatus.ACTIVE
        ):
            data = FlutterwaveProvider().cancel_subscription(sub_id)
            subscription.status = PaymentStatus.PAUSED
        subscription.save()
        return Response(status=status.HTTP_200_OK, data=data)


class FlutterwaveWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # print("request: ",request.data)
        FlutterwaveProvider().webhook(request)
        return Response(status=status.HTTP_200_OK)


class PaymentListAPIView(ListAPIView):
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        payments = SubscriptionPayment.objects.filter(user=user)
        return payments  # super().get_queryset()


class UpdateSubscriptionPlanView(generics.UpdateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(active=True)


class ListSubscriptionPlanView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(active=True)


class ListFeatureView(generics.ListAPIView):
    permission_classes = []
    serializer_class = FeatureSerializer
    queryset = Feature.objects.filter()


class CreateFeatureView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = FeatureSerializer
    # queryset = Feature.objects.filter(active=True)


class RetrieveUpdateDeleteFeatureView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    serializer_class = FeatureSerializer
    queryset = Feature.objects.filter()
