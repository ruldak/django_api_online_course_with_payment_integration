from rest_framework.views import exception_handler
from .response_util import error_response, validation_error_response
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            return validation_error_response(response.data, response.status_code)
        else:
            return error_response(response.data.get('detail', 'An error occurred'), response.status_code)

    return response
