from payment.models import (
    SubscriptionPayment,
    PaymentStatus,
    SubscriptionPlan,
    Feature,
)
from user.factories import create_test_user


def creat_test_payment_plan(
    name="Diamond Plan", amount=100, plan_id="12345", active=True
):
    payment_plan = SubscriptionPlan.objects.create(
        name=name, amount=amount, plan_id=plan_id, active=active
    )
    return payment_plan


def creat_test_payment(
    plan=None,
    user=None,
    amount=1000,
    status=PaymentStatus.PENDING,
):
    user = user or create_test_user()
    plan = plan or creat_test_payment_plan()
    payment = SubscriptionPayment.objects.create(
        plan=plan,
        user=user,
        amount=amount,
        status=status,
    )
    return payment


def create_test_feature(
    name=None, bronze=None, silver=None, gold=None, platinum=None, pay_as_you_go=None
):
    name = name or "test_feature"
    bronze = bronze or True
    silver = silver or True
    gold = gold or True
    platinum = platinum or True
    pay_as_you_go = pay_as_you_go or True

    feature = Feature.objects.create(
        name=name,
        bronze=bronze,
        silver=silver,
        gold=gold,
        platinum=platinum,
        pay_as_you_go=pay_as_you_go,
    )
    return feature
