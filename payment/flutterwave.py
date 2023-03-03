import requests
import uuid
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from core.exceptions import ApiRequestException
from .gateway import Gateway
from user.models import User
from .models import SubscriptionPayment, PaymentStatus, RecurringSubscriptionPayment
from rest_framework.exceptions import ValidationError
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger("main")
FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3/"


class FlutterwaveAPI:
    def request(self, method, path, payload={}, params={}):
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.FLUTTERWAVE_PRIVATE_KEY}",
            "Content-Type": "application/json",
        }
        url = FLUTTERWAVE_BASE_URL + path
        response = requests.request(
            method, url, json=payload, params=params, headers=headers
        )
        if response.status_code != 200:
            ApiRequestException(
                url=url,
                method=method,
                body=payload,
                response=response.content,
                status_code=response.status_code,
            )
        response_dict = response.json()
        if response_dict["status"] != "success":
            raise ApiRequestException(
                url=url,
                method=method,
                body=payload,
                response=response.content,
                status_code=response.status_code,
            )
        return response_dict


class FlutterwaveProvider(Gateway):
    def __init__(self) -> None:
        super().__init__()
        self.extra = {}
        self.api = FlutterwaveAPI()

    def get_all_subscriptions(self):
        response = self.api.request("GET", "subscriptions")
        return response["data"]

    def create_subscription_plan(self, name, amount, interval="monthly"):
        api = FlutterwaveAPI()
        if settings.LOCAL:
            interval = "daily"
        payload = {
            "amount": amount,
            "name": name,
            "interval": interval,
            "currency": "USD",
        }
        response = api.request("POST", "payment-plans", payload)
        plan = response["data"]
        return plan

    # status (cancel, active)
    def update_subscription_plan(self, plan_id, name, status):
        api = FlutterwaveAPI()
        payload = {
            "name": name,
            "status": status,
        }
        response = api.request("PUT", f"payment-plans/{plan_id}", payload)
        plan = response["data"]
        return plan

    def get_subscription_plan(self, plan_id, api=None):
        url = f"payment-plans/{plan_id}"
        response = self.api.request("GET", url)
        return response["data"]

    def _create_subscription(self, email, plan_id, total_amount, currency):
        tx_ref = str(uuid.uuid4())
        payment_payload = {
            "tx_ref": tx_ref,
            "amount": total_amount,
            "currency": currency,
            "redirect_url": settings.SUBSCRIPTION_REDIRECT_URL,
            "payment_options": "card",
            "payment_plan": plan_id,
            "meta": {
                "email": email,
            },
            "customer": {"email": email, "name": email},
            "customizations": {
                "title": "HomeCare Subscription Payment",
                "description": "Middleout isn't free. Pay the price",
                "logo": "https://www.dokto.com/static/media/Dokto3.2248ed381b6c65f7353b.png",
            },
        }
        response_dict = self.api.request("POST", "payments", payment_payload)

        payment_link = response_dict["data"]["link"]

        return tx_ref, payment_link

    def init_subscription(self, email, plan):
        plan_id = plan["id"]
        amount = plan["amount"]
        currency = plan["currency"]
        data = self._create_subscription(
            email=email, plan_id=plan_id, total_amount=amount, currency=currency
        )
        return data

    def subscribe(self,  email, plan):
        plan_from_response = self.get_subscription_plan(plan_id=plan.plan_id)
        subcription_data = self.init_subscription(email, plan=plan_from_response)
        SubscriptionPayment.objects.create(
            email=email,
            payment_ref=subcription_data[0],
            amount=plan_from_response["amount"],
            status=PaymentStatus.PENDING,
            plan=plan,
        )
        return subcription_data

    def cancel_subscription(self, subscription_id):
        path = f"subscriptions/{subscription_id}/cancel"
        data = self.api.request("PUT", path, {})
        return data

    def activate_subscription(self, subscription_id):
        path = f"subscriptions/{subscription_id}/activate"
        data = self.api.request("PUT", path, {})
        return data

    def _get_subscription_id_for_subscription_history(
        self, subscription: SubscriptionPayment, *args, **kwargs
    ):
        params = {**kwargs}
        res = self.api.request("GET", "subscriptions", {}, params=params)
        flutter_subscriptions = res["data"]

        flutter_subscription = None
        for sub in flutter_subscriptions:
            if sub["customer"]["customer_email"] == subscription.user.email:
                flutter_subscription = sub

        return flutter_subscription["id"]

    def _verify_webhook(self, request):
        # print("verifying webhook", request.data)
        tx_ref = request.data["data"]["tx_ref"]  # "4009243"
        sub_payment_by_tx_ref = SubscriptionPayment.objects.filter(
            payment_ref=tx_ref
        )
        url = f"transactions/verify_by_reference?tx_ref={tx_ref}"
        verify_data = FlutterwaveAPI().request(method="GET", path=url)
        logger.info(f"REQUEST HEADER  ({tx_ref}): " + json.dumps(request.headers))

        if (
            request.headers.get("Verif-Hash")
            != settings.FLUTTERWAVE_WEBHOOK_VERIFICATION_HASH
        ):
            logger.info(f"reason: webhook verification hash failed for tx_ref {tx_ref}, flutter_header={request.headers.get('Verif-Hash')}  env={settings.FLUTTERWAVE_WEBHOOK_VERIFICATION_HASH} ")
            raise AuthenticationFailed()
        if (
            verify_data["data"]["status"] != "successful"
            or "Approved" not in verify_data["data"]["processor_response"]
        ):
            logger.info(f"reason: payment verification failed for tx_ref {tx_ref}")
            sub_payment_by_tx_ref.update(status=PaymentStatus.FAILED)
            raise AuthenticationFailed()

        return True

    def webhook(self, request):

        logger.info("WEBHOOK_REQUEST_DATA: " + json.dumps(request.data))
        logger.info("WEBHOOK_REQUEST_HEADER_DATA: " + json.dumps(request.header))
        self._verify_webhook(request=request)
        webhook_data = request.data
        transaction_id = webhook_data["data"]["id"]
        start_time_string = webhook_data["data"]['created_at']
        start_time = datetime.strptime(start_time_string, '%Y-%m-%dT%H:%M:%S.%f%z')
        subscription_interval = timedelta(hours=1) if settings.LOCAL else timedelta(days=30)
        end_time = start_time + subscription_interval 

        payments = SubscriptionPayment.objects.filter(
            payment_ref=request.data["data"]["tx_ref"]
        ).select_related("plan")
        payment = payments.first()
        plan_id = payment.plan.plan_id
        if not payments.exists():
            raise ValidationError("record not found")
        extra_gateway_values = ""

        if not payment.extra_gateway_values:
            sub_id = self._get_subscription_id_for_subscription_history(
                subscription=payment, plan=plan_id, transaction_id=transaction_id
            )
            extra_gateway_values = json.dumps(
                {"sub_id": sub_id, "transaction_id": transaction_id}
            )
        payments.update(
            paid=True,
            status=PaymentStatus.ACTIVE,
            extra_gateway_values=extra_gateway_values,
            subscription_start=start_time,
            subscription_end=end_time,
        )
        payment.add_new_payment(ref = transaction_id, start = start_time, end= end_time)
        return request.data
