from rest_framework import serializers
from .models import SubscriptionPayment, SubscriptionPlan, Feature

from .flutterwave import FlutterwaveProvider


class SubscriptionChargeSerializer(serializers.Serializer):
    approval_url = serializers.SerializerMethodField(read_only=True)
    plan_id = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)

    def get_approval_url(self, obj):
        return self.context.get("approval_url")


class ActivateCancelSubscriptionViewSerializer(serializers.Serializer):
    status = serializers.BooleanField(write_only=True)
    subscription = serializers.UUIDField()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"
        read_only_fields = ["is_deleted", "deleted_at"]
        extra_kwargs = {
            "plan_id": {"read_only": True, "required": False},
            "name": {"read_only": True, "required": False},
        }

    def update(self, instance, validated_data):
        amount = validated_data.get("amount")
        name = instance.name
        response = FlutterwaveProvider().create_subscription_plan(
            name=name, amount=float(amount)
        )
        plan_id = str(response["id"])
        subscription_plan = SubscriptionPlan.objects.create(
            name=name, amount=amount, plan_id=plan_id
        )
        instance.active = False
        instance.save()
        return subscription_plan


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer()

    class Meta:
        model = SubscriptionPayment
        fields = "__all__"


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"
