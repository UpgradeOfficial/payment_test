from django.test import TestCase
from unittest.mock import patch, Mock
from user.factories import create_test_user
from .factories import create_test_feature, creat_test_payment, creat_test_payment_plan
from django.urls.base import reverse
from .models import Feature, SubscriptionPlan, PaymentStatus, SubscriptionPayment
from user.models import User

from .flutterwave import FlutterwaveProvider
from rest_framework.exceptions import AuthenticationFailed


get_plan_mock_data = {
    "status": "success",
    "message": "Payment plan created",
    "data": {
        "id": 3807,
        "name": "the akhlm postman plan 2",
        "amount": 5000,
        "interval": "monthly",
        "duration": 48,
        "status": "active",
        "currency": "NGN",
        "plan_token": "rpp_12d2ef3d5ac1c13b9d30",
        "created_at": "2020-01-16T18:08:19.000Z",
    },
}

get_payment_success_data = {
    "status": "success",
    "message": "Transaction fetched successfully",
    "data": {
        "id": 1163068,
        "tx_ref": "akhlm-pstmn-blkchrge-xx6",
        "flw_ref": "FLW-M03K-02c21a8095c7e064b8b9714db834080b",
        "device_fingerprint": "N/A",
        "amount": 3000,
        "currency": "NGN",
        "charged_amount": 3000,
        "app_fee": 1000,
        "merchant_fee": 0,
        "processor_response": "Approved",
        "auth_model": "noauth",
        "ip": "pstmn",
        "narration": "Kendrick Graham",
        "status": "successful",
        "payment_type": "card",
        "created_at": "2020-03-11T19:22:07.000Z",
        "account_id": 73362,
        "amount_settled": 2000,
        "card": {
            "first_6digits": "553188",
            "last_4digits": "2950",
            "issuer": " CREDIT",
            "country": "NIGERIA NG",
            "type": "MASTERCARD",
            "token": "flw-t1nf-f9b3bf384cd30d6fca42b6df9d27bd2f-m03k",
            "expiry": "09/22",
        },
        "customer": {
            "id": 252759,
            "name": "Kendrick Graham",
            "phone_number": "0813XXXXXXX",
            "email": "user@example.com",
            "created_at": "2020-01-15T13:26:24.000Z",
        },
    },
}

webhook_success_data = {
    "event": "charge.completed",
    "txRef": "bda7665f-1b6e-4d10-a5c6-b71e6736dab7",  # txRef when passed by flutterwave
    "data": {
        "id": 285959875,
        "tx_ref": "bda7665f-1b6e-4d10-a5c6-b71e6736dab7",  # txRef when passed by flutterwave
        "txRef": "bda7665f-1b6e-4d10-a5c6-b71e6736dab7",  # txRef when passed by flutterwave
        "flw_ref": "PeterEkene/FLW270177170",
        "device_fingerprint": "a42937f4a73ce8bb8b8df14e63a2df31",
        "amount": 100,
        "currency": "NGN",
        "charged_amount": 100,
        "app_fee": 1.4,
        "merchant_fee": 0,
        "processor_response": "Approved by Financial Institution",
        "auth_model": "PIN",
        "ip": "197.210.64.96",
        "narration": "CARD Transaction ",
        "status": "successful",
        "payment_type": "card",
        "created_at": "2020-07-06T19:17:04.000Z",
        "account_id": 17321,
        "customer": {
            "id": 215604089,
            "name": "Yemi Desola",
            "phone_number": None,
            "email": "user@gmail.com",
            "created_at": "2020-07-06T19:17:04.000Z",
        },
        "card": {
            "first_6digits": "123456",
            "last_4digits": "7889",
            "issuer": "VERVE FIRST CITY MONUMENT BANK PLC",
            "country": "NG",
            "type": "VERVE",
            "expiry": "02/23",
        },
    },
}

subscribe_return_data = (
    "flw_id_of_subcription",
    "http://localhost:8000/api/v1/flw/flw_",
)

mock_activate_subscription_data = {
    "status": "success",
    "message": "Subscription activated",
    "data": {
        "id": 4147,
        "amount": 2000,
        "customer": {"id": 247546, "customer_email": "developers@flutterwavego.com"},
        "plan": 3657,
        "status": "active",
        "created_at": "2019-12-31T17:00:55.000Z",
    },
}
mock_cancel_subscription_data = {
    "status": "success",
    "message": "Subscription cancelled",
    "data": {
        "id": 4147,
        "amount": 2000,
        "customer": {"id": 247546, "customer_email": "developers@flutterwavego.com"},
        "plan": 3657,
        "status": "cancelled",
        "created_at": "2019-12-31T17:00:55.000Z",
    },
}


# Create your tests here.
class TestFlutterwaveSubscriptionPayment(TestCase):
    @patch(
        "payment.flutterwave.FlutterwaveProvider.subscribe",
        return_value=subscribe_return_data,
    )
    def test_subscription_api(self, mock_create_sub):
        user = create_test_user()
        self.client.force_login(user)
        plan = creat_test_payment_plan()
        data = {"plan_id": plan.plan_id}
        path = reverse("payment:subscribe")
        res = self.client.post(path, data=data)
        res_body = res.json()
        self.assertEqual(res_body["approval_url"], subscribe_return_data[1])

    @patch(
        "payment.flutterwave.FlutterwaveAPI.request",
        return_value=get_payment_success_data,
    )
    def test_verify_webhook(self, mock_get_payment_data):
        request = Mock(
            data=webhook_success_data, headers={"Verif-Hash": "hhhhhhhhhhhhhhhhhhhh"}
        )

        # Test with correct secret key
        with self.settings(
            FLUTTERWAVE_WEBHOOK_VERIFICATION_HASH="hhhhhhhhhhhhhhhhhhhh"
        ):
            FlutterwaveProvider()._verify_webhook(request)
            self.assertTrue(True)

        # Test with wrong secret key
        with self.settings(FLUTTERWAVE_WEBHOOK_VERIFICATION_HASH="wrong-key"):
            self.assertRaises(
                AuthenticationFailed,
                lambda: FlutterwaveProvider()._verify_webhook(request),
            )

 

    def test_list_all_subscription(self):
        user = create_test_user()
        user2 = create_test_user()
        creat_test_payment(user=user)
        creat_test_payment(user=user)
        creat_test_payment(user=user2)
        creat_test_payment(user=user2)
        creat_test_payment(user=user2)
        self.client.login(user)
        path = reverse("payment:all_payment")
        res = self.client.get(path)
        res_body = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res_body), 2)


class TestFeature(TestCase):
    def test_list_all_feature(self):
        create_test_feature()
        create_test_feature()
        create_test_feature()
        create_test_feature()
        path = reverse("payment:list-features")
        res = self.client.get(path)
        res_body = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res_body), 4)

    def test_create_feature(self):
        admin_user = create_test_user()
        self.client.force_login(admin_user)
        path = reverse("payment:create-feature")
        data = {
            "name": "My test feature",
            "bronze": True,
            "silver": True,
            "gold": True,
            "platinum": True,
        }
        res = self.client.post(path, data=data)
        res_body = res.json()

        self.assertEqual(res.status_code, 201)
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(res_body["name"], data["name"])
        self.assertEqual(res_body["bronze"], data["bronze"])
        self.assertEqual(res_body["silver"], data["silver"])
        self.assertEqual(res_body["platinum"], data["platinum"])
        self.assertEqual(res_body["pay_as_you_go"], data.get("pay_as_you_go", False))

    def test_create_feature_non_admin_user(self):
        admin_user = create_test_user()
        self.client.force_login(admin_user)
        path = reverse("payment:create-feature")
        data = {
            "name": "My test feature",
            "bronze": True,
            "silver": True,
            "gold": True,
            "platinum": True,
        }

        res = self.client.post(path, data=data)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Feature.objects.count(), 0)

    def test_update_feature_by_admin(self):
        admin_user = create_test_user()
        self.client.force_login(admin_user)
        feature = create_test_feature()
        path = reverse("payment:update-delete-feature", kwargs={"pk": str(feature.pk)})
        data = {
            "name": "My new changed feature",
            "bronze": False,
            "platinum": False,
            "silver": False,
        }
        res = self.client.patch(path, data=data, content_type="application/json")
        res_body = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_body["name"], data.get("name"))
        self.assertEqual(res_body["bronze"], data.get("bronze"))
        self.assertEqual(res_body["platinum"], data.get("platinum"))
        self.assertEqual(res_body["silver"], data.get("silver"))
        self.assertEqual(res_body["gold"], data.get("gold", True))
        self.assertEqual(res_body["pay_as_you_go"], data.get("pay_as_you_go", True))

    def test_delete_feature_by_admin(self):
        admin_user = create_test_user()
        self.client.force_login(admin_user)
        feature = create_test_feature()
        path = reverse("payment:update-delete-feature", kwargs={"pk": str(feature.pk)})
        res = self.client.delete(path, content_type="application/json")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Feature.objects.count(), 0)


class TestSubscriptionPlan(TestCase):
    def test_list_all_subscription_plan(self):
        path = reverse("payment:list-subscription-plan")
        response = self.client.get(path)
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 5)

    @patch(
        "payment.flutterwave.FlutterwaveProvider.create_subscription_plan",
        return_value=get_plan_mock_data["data"],
    )
    def test_update_subcription_plan(self, mock_get_payment_data):
        admin_user = create_test_user()
        self.client.force_login(admin_user)
        plan = SubscriptionPlan.objects.get(name="BRONZE")
        path = reverse("payment:update-subscription-plan", kwargs={"pk": plan.id})
        data = {"amount": 211}
        response = self.client.patch(path, data=data, content_type="application/json")
        # response_data = response.json()
        subscription_plans = SubscriptionPlan.objects.all()
        all_bronze_plan = subscription_plans.filter(name="BRONZE")
        old_bronze_plan = all_bronze_plan.filter(name="BRONZE", amount=100).first()
        new_bronze_plan = all_bronze_plan.filter(name="BRONZE", amount=211).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(subscription_plans.count(), 6)
        self.assertEqual(all_bronze_plan.count(), 2)
        self.assertEqual(new_bronze_plan.plan_id, str(get_plan_mock_data["data"]["id"]))
        self.assertEqual(new_bronze_plan.amount, data["amount"])
        self.assertEqual(new_bronze_plan.amount, data["amount"])
        self.assertEqual(new_bronze_plan.active, True)
        self.assertEqual(old_bronze_plan.active, False)


class TestActivateCancelSubscriptionPlan(TestCase):
    @patch(
        "payment.flutterwave.FlutterwaveProvider.cancel_subscription",
        return_value=mock_cancel_subscription_data,
    )
    def test_cancel_subscription(self, mock_cancel_subscription):
        subcription = creat_test_payment()
        subcription.paid = True
        subcription.extra_gateway_values = (
            '{"sub_id": "123456", "transaction_id": "123456"}'
        )
        subcription.status = PaymentStatus.ACTIVE
        subcription.save()
        self.client.force_login(subcription.user)
        path = reverse("payment:unsubscribe_or_resubscribe")
        data = {"status": False, "subscription": str(subcription.id)}

        response = self.client.post(path, data=data)
        response_data = response.json()
        subscription_from_db = SubscriptionPayment.objects.get(id=subcription.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(subscription_from_db.status, PaymentStatus.PAUSED)
        self.assertEqual(
            response_data["data"]["status"],
            mock_cancel_subscription_data["data"]["status"],
        )

    @patch(
        "payment.flutterwave.FlutterwaveProvider.activate_subscription",
        return_value=mock_activate_subscription_data,
    )
    def test_active_subscription(self, mock_activate_subscription):
        subcription = creat_test_payment()
        subcription.paid = True
        subcription.extra_gateway_values = (
            '{"sub_id": "123456", "transaction_id": "123456"}'
        )
        subcription.status = PaymentStatus.PAUSED
        subcription.save()
        self.client.force_login(subcription.user)
        path = reverse("payment:unsubscribe_or_resubscribe")
        data = {"status": True, "subscription": str(subcription.id)}
        response = self.client.post(path, data=data)
        response_data = response.json()
        subscription_from_db = SubscriptionPayment.objects.get(id=subcription.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(subscription_from_db.status, PaymentStatus.ACTIVE)
        self.assertEqual(
            response_data["data"]["status"],
            mock_activate_subscription_data["data"]["status"],
        )

    @patch(
        "payment.flutterwave.FlutterwaveProvider.activate_subscription",
        return_value=mock_activate_subscription_data,
    )
    def test_active_subscription_unauthorized_user(self, mock_activate_subscription):
        subcription = creat_test_payment()
        subcription.paid = True
        subcription.extra_gateway_values = (
            '{"sub_id": "123456", "transaction_id": "123456"}'
        )
        subcription.status = PaymentStatus.PAUSED
        subcription.save()
        path = reverse("payment:unsubscribe_or_resubscribe")
        data = {"status": True, "subscription": str(subcription.id)}
        response = self.client.post(path, data=data)
        self.assertEqual(response.status_code, 401)

    @patch(
        "payment.flutterwave.FlutterwaveProvider.activate_subscription",
        return_value=mock_activate_subscription_data,
    )
    def test_active_subscription_by_another_user(self, mock_activate_subscription):
        subcription = creat_test_payment()
        user = create_test_user()
        self.client.force_login(user)
        subcription.paid = True
        subcription.extra_gateway_values = (
            '{"sub_id": "123456", "transaction_id": "123456"}'
        )
        subcription.status = PaymentStatus.PAUSED
        subcription.save()
        path = reverse("payment:unsubscribe_or_resubscribe")
        data = {"status": True, "subscription": str(subcription.id)}
        response = self.client.post(path, data=data)
        response_data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response_data["message"],
            "Either subscription does not exist \
                    or you are not the owner of the subscription or hasn't been paid.",
        )

    @patch(
        "payment.flutterwave.FlutterwaveProvider.activate_subscription",
        return_value=mock_activate_subscription_data,
    )
    def test_active_subscription_that_hasnot_been_paid(
        self, mock_activate_subscription
    ):
        subcription = creat_test_payment()
        self.client.force_login(subcription.user)
        subcription.paid = False
        subcription.extra_gateway_values = (
            '{"sub_id": "123456", "transaction_id": "123456"}'
        )
        subcription.status = PaymentStatus.PAUSED
        subcription.save()
        path = reverse("payment:unsubscribe_or_resubscribe")
        data = {"status": True, "subscription": str(subcription.id)}
        response = self.client.post(path, data=data)
        response_data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response_data["message"],
            "Either subscription does not exist \
                    or you are not the owner of the subscription or hasn't been paid.",
        )
