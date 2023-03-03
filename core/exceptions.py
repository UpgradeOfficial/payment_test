from rest_framework.exceptions import ValidationError
import logging


class NotImplementedException(ValidationError):
    def __init__(self, detail="Feature not implemented", code="NotImplemented"):
        super(NotImplementedException, self).__init__(detail, code)


class ApiRequestException(ValidationError):
    def __init__(
        self,
        url=None,
        method=None,
        header=None,
        body=None,
        response=None,
        status_code=None,
        detail="Gateway Error",
        code="Gateway Error",
    ):
        super(ApiRequestException, self).__init__(detail, code)
        logging.error(
            f"API_EXCEPTION  url:{url}, method:{method}, body: {body},\
             response: {response}, status_code: {status_code}"
        )
