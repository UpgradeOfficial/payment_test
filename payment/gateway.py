import logging
from rest_framework.exceptions import ValidationError
from .models import PaymantProvider  # , PaymentPlanType


class GatewayException(ValidationError):
    def __init__(self, detail=None, code=None):
        super(GatewayException, self).__init__(detail, code)
        logging.warning(f"Gateway Error: {code} Detail: {detail}")


class Gateway:
    # def get_plan_name(self, abbr):
    #     plan_type_dict = {"B": PaymentPlanType.BRONZE}
    #     return plan_type_dict.get(abbr, PaymentPlanType.BRONZE)

    def cancel_subscription(self):
        raise NotImplementedError

    def _verify_webhook(self, request):
        raise NotImplementedError

    @staticmethod
    def get_payment_gateway(provider):
        from .flutterwave import FlutterwaveProvider

        providers_dict = {
            PaymantProvider.FLUTTERWAVE: FlutterwaveProvider(),
        }
        provider = providers_dict[provider]
        return provider

    # def subscribe(self, payment_method, user):
    #     gateway = Gateway.get_payment_gateway(payment_method)
    #     sub_id, approval_url = gateway.subscribe(user, )
    #     return sub_id, approval_url
